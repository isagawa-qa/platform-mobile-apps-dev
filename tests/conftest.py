"""
Pytest configuration and fixtures.

Provides reusable fixtures for test execution:
- driver: Appium session for the resolved device profile
- config: the whole environment_config.json document, unexpanded
- device: --platform resolved to one venue block, ${VAR} expanded
- test_users: Test user credentials
- workflow_data: The calling workflow's test data from tests/{workflow}/data/
- mobile: MobileInterface wrapper with all dependencies
- artifacts_dir: where failure evidence is written

This module is the ONLY place a session is built and the ONLY place failure
evidence is captured. Screenshots and page source belong here, never to the
Interface and never to a Screen.
"""

import ast
import os
import re
import sys
import json
import logging
import pytest
from pathlib import Path
from datetime import datetime

# Project root and framework path
PROJECT_ROOT = Path(__file__).parent.parent
FRAMEWORK_PATH = str(PROJECT_ROOT / "framework")
sys.path.insert(0, FRAMEWORK_PATH)

from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.options.ios import XCUITestOptions
from interfaces.mobile_interface import MobileInterface

logger = logging.getLogger("MobileInterface")

CONFIG_PATH = PROJECT_ROOT / "framework" / "resources" / "config" / "environment_config.json"

# Venue-level keys. They configure the venue; they are never W3C capabilities.
_NON_CAPABILITY_KEYS = frozenset({
    "server_url", "requires_host_os", "runner", "credentials", "note",
    "venue", "platformKey", "family", "markers", "default_app",
})

_VAR = re.compile(r"\$\{([A-Z0-9_]+)(?::-([^}]*))?\}")

# Capabilities that by themselves decide which app the session launches. If a
# venue block sets any of them, app resolution is skipped entirely.
_LAUNCH_KEYS = frozenset({"appium:app", "appium:bundleId", "appium:appPackage"})

_PHASE_REPORT_KEY = pytest.StashKey[dict]()


# ------------------------------------------------------------------------------
# Command line options
# ------------------------------------------------------------------------------

def pytest_addoption(parser):
    """Configure custom command line options for running tests.

    Falls back to environment variables (.env) when CLI flags are not provided.
    There is deliberately no choices= list: legal values are exactly the keys of
    config["platforms"], so adding a profile is a config edit, never a code edit.
    """
    parser.addoption("--platform", action="store",
                     default=os.environ.get("PLATFORM"),
                     help="Platform key from environment_config.json "
                          "(default: its default_platform)")


# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------

def _expand_env(value):
    """Substitute ${VAR} and ${VAR:-default} from os.environ, failing loudly.

    A missing variable with no default names both the variable and .env, so the
    fix is in the message rather than in a stack trace.
    """
    if isinstance(value, dict):
        return {k: _expand_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env(v) for v in value]
    if not isinstance(value, str):
        return value

    def sub(match):
        name, default = match.group(1), match.group(2)
        if name in os.environ:
            return os.environ[name]
        if default is not None:
            return default
        pytest.fail(f"{name} is not set; set it in .env")

    return _VAR.sub(sub, value)


def _resolve_app_capabilities(config, app_name, family, venue):
    """Map a platform's default_app to the capabilities that launch it.

    Without this the session attaches to whatever is already on the device and
    the `apps` registry is decorative, which is what it was until this shipped.

    Rules, in order:
      - No default_app (the -web platforms) means no app: those drive a browser.
      - The cloud venue takes a provider app reference, never a local path.
      - Otherwise a path wins and `appium:app` installs and launches it.
      - Only when there is no path does the identifier apply, launching an app
        already installed. Expansion is lazy for exactly this reason: app_id is
        often ${IOS_BUNDLE_ID} with no default, and expanding it eagerly would
        fail a local run whose path was perfectly good.
    """
    if not app_name:
        return {}

    apps = config.get("apps", {})
    if app_name not in apps:
        pytest.fail(
            f"default_app {app_name!r} is not a key of apps in {CONFIG_PATH}"
        )
    entry = apps[app_name]

    if venue == "cloud":
        reference = _expand_env(entry.get("cloud", {}).get(family, ""))
        if not reference:
            pytest.fail(
                f"app {app_name!r} has no cloud reference for {family!r}; "
                f"set it under apps.{app_name}.cloud.{family} in {CONFIG_PATH}"
            )
        return {"appium:app": reference}

    slot = entry.get(family)
    if not slot:
        pytest.fail(
            f"app {app_name!r} has no {family!r} entry in {CONFIG_PATH}"
        )

    if slot.get("path"):
        path = Path(_expand_env(slot["path"]))
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        if not path.exists():
            pytest.fail(
                f"app artifact for {app_name!r} ({family}) is not at {path}. "
                f"Fetch it — see SETUP.md Step 3 — or set the path override in .env."
            )
        return {"appium:app": str(path)}

    if slot.get("app_id"):
        key = "appium:bundleId" if family == "ios" else "appium:appPackage"
        return {key: _expand_env(slot["app_id"])}

    pytest.fail(
        f"app {app_name!r} ({family}) declares neither a path nor an app_id "
        f"in {CONFIG_PATH}"
    )


def _build_options(profile):
    """Build the Appium options object for one resolved device profile.

    Capabilities live under the block's "capabilities" key - the nested shape the
    config actually ships. Venue-level keys (server_url, requires_host_os,
    runner, credentials) configure the venue and are never forwarded as W3C
    capabilities.

    Every capability comes from config, so adding one is a config edit, never a
    code edit. The only literal here is the automation-name discriminator.
    """
    capabilities = profile.get("capabilities", {})
    if capabilities.get("appium:automationName") == "XCUITest":
        options = XCUITestOptions()
    else:
        options = UiAutomator2Options()
    for key, value in capabilities.items():
        if key not in _NON_CAPABILITY_KEYS:
            options.set_capability(key, value)
    return options


def _capture_failure_evidence(node, drv, artifacts_dir):
    """Screenshot + page source when the test failed. Raises nothing, ever.

    A failure while documenting a failure must never mask the original, so every
    path here is swallowed deliberately.
    """
    try:
        report = node.stash.get(_PHASE_REPORT_KEY, {})
        if not any(r.failed for r in report.values()):
            return
        stem = re.sub(r"[^A-Za-z0-9_.-]", "_", node.nodeid)[:120]
        shots = artifacts_dir / "screenshots"
        source = artifacts_dir / "page_source"
        shots.mkdir(parents=True, exist_ok=True)
        source.mkdir(parents=True, exist_ok=True)
        try:
            drv.save_screenshot(str(shots / f"{stem}.png"))
        except Exception:
            pass
        try:
            (source / f"{stem}.xml").write_text(drv.page_source, encoding="utf-8")
        except Exception:
            pass
    except Exception:
        pass


def _register_dynamic_markers(config):
    """
    Scan test files and auto-register any pytest markers found.

    Allows AI-generated tests to use custom markers without manual pytest.ini updates.
    """
    markers = set()
    tests_dir = PROJECT_ROOT / "tests"

    for test_file in tests_dir.rglob("*.py"):
        try:
            tree = ast.parse(test_file.read_text(encoding="utf-8"))

            for node in ast.walk(tree):
                if (isinstance(node, ast.Attribute) and
                    isinstance(node.value, ast.Attribute) and
                    node.value.attr == "mark" and
                    isinstance(node.value.value, ast.Name) and
                    node.value.value.id == "pytest"):
                    markers.add(node.attr)
        except (SyntaxError, UnicodeDecodeError):
            pass

    for marker in markers:
        config.addinivalue_line("markers", f"{marker}: Auto-discovered marker")


# ------------------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------------------

@pytest.fixture(scope="session")
def config():
    """Load the whole environment configuration document, unexpanded.

    Session-scoped: Loaded once per test session. Expansion is deliberately lazy
    and happens in `device`, so a missing cloud credential cannot fail a local run.
    """
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        yield json.load(f)


@pytest.fixture(scope="session")
def device(request, config):
    """Resolve --platform to one venue block with ${VAR} expanded.

    Failures are pytest.fail rather than ValueError: a misconfigured venue must
    read as a setup failure with the fix in the message.
    """
    name = request.config.getoption("--platform") or config["default_platform"]
    if name not in config["platforms"]:
        pytest.fail(f"--platform {name!r} is not a key of platforms in {CONFIG_PATH}")

    platform = config["platforms"][name]
    venue = _expand_env(platform["venue"])
    block = platform.get(venue)
    if not block or "note" in block:
        reason = block.get("note") if block else "block missing"
        pytest.fail(f"platform {name!r} has no usable {venue!r} venue: {reason}")

    required_os = block.get("requires_host_os")
    if required_os and sys.platform != required_os:
        alternatives = [
            v for v in ("remote", "cloud")
            if platform.get(v) and not platform[v].get("requires_host_os")
        ]
        pytest.fail(
            f"platform {name!r} venue {venue!r} requires host OS {required_os!r} "
            f"but this host is {sys.platform!r}. iOS tooling does not exist off "
            f"macOS, so no amount of configuration makes this venue work here. "
            f"Use a venue that reaches a machine which has it: "
            f"{', '.join(alternatives) or 'none configured'} — "
            f"set the venue via the platform's venue variable in .env."
        )

    resolved = _expand_env(dict(block))
    resolved["platformKey"] = name
    resolved["venue"] = venue
    resolved["family"] = platform.get("family", "")
    resolved["markers"] = platform.get("markers", [])
    resolved["default_app"] = platform.get("default_app")

    # The app under test is a property of the platform, not of the venue block,
    # so it is resolved here and merged in. An explicit capability in config
    # always wins: a venue that names its own app is making a deliberate
    # statement this must not overwrite.
    #
    # The explicit check comes FIRST and short-circuits resolution. Resolving
    # and then deferring would be wrong, because resolution fails hard on a
    # missing artifact - so an override would be unreachable in exactly the
    # case it exists for, which is pointing somewhere other than the default.
    capabilities = dict(resolved.get("capabilities", {}))
    if not _LAUNCH_KEYS & capabilities.keys():
        capabilities.update(
            _resolve_app_capabilities(
                config, resolved["default_app"], resolved["family"], venue
            )
        )
    resolved["capabilities"] = capabilities

    yield resolved


@pytest.fixture(scope="session")
def artifacts_dir():
    """The directory failure evidence is written to, created on first use."""
    path = PROJECT_ROOT / "artifacts"
    path.mkdir(parents=True, exist_ok=True)
    yield path


@pytest.fixture
def driver(request, device, artifacts_dir):
    """Create and teardown the Appium session for each test.

    Function-scoped: template parity and per-test isolation, so a failed test's
    artifacts describe its own session.

    Teardown order is fixed: capture evidence first, quit() second, both in
    finally. A screenshot cannot be taken after quit().
    """
    options = _build_options(device)
    drv = webdriver.Remote(device["server_url"], options=options)
    try:
        yield drv
    finally:
        _capture_failure_evidence(request.node, drv, artifacts_dir)
        drv.quit()


@pytest.fixture(scope="session")
def test_users():
    """
    Load test user credentials.

    Session-scoped: Loaded once per test session.
    """
    users_path = PROJECT_ROOT / "tests" / "data" / "test_users.json"
    with open(users_path, "r", encoding="utf-8") as f:
        yield json.load(f)


@pytest.fixture(scope="module")
def workflow_data(request):
    """
    Load the calling workflow's test data from tests/{workflow}/data/.

    Every JSON file in the test module's data/ folder is keyed by its
    file name without .json: data/new_customer.json is
    workflow_data["new_customer"]. Workflows use this instead of
    adding their own conftest.py.

    Module-scoped: Loaded once per test module.
    """
    data_dir = request.path.parent / "data"
    data_files = sorted(data_dir.glob("*.json"))
    if not data_files:
        pytest.fail(f"workflow_data: no JSON files found in {data_dir}")

    data = {}
    for data_file in data_files:
        with open(data_file, "r", encoding="utf-8") as f:
            data[data_file.stem] = json.load(f)
    yield data


@pytest.fixture
def mobile(driver, device):
    """Create MobileInterface with driver, device profile, logger and platform.

    `platform` is passed EXPLICITLY rather than read from driver.capabilities:
    the Interface's constructor takes it as a fourth argument so a stub driver
    need not fake capabilities. Derived from the block's platformName.
    """
    family = device.get("capabilities", {}).get("platformName", "").lower()
    yield MobileInterface(driver, device, logger, family)


# ==============================================================================
# HTML REPORT ENHANCEMENTS
# ==============================================================================
def pytest_html_report_title(report):
    """Customize HTML report title."""
    report.title = "Isagawa QA Platform (Mobile) - Test Report"


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    """Add custom metadata to report header and auto-register markers."""
    platform_key = config.getoption("--platform") or ""
    venue = device_name = automation = server = ""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            document = json.load(f)
        platform_key = platform_key or document.get("default_platform", "")
        profile = document.get("platforms", {}).get(platform_key, {})
        venue = _expand_env(profile.get("venue", ""))
        block = profile.get(venue, {}) or {}
        caps = block.get("capabilities", {})
        device_name = caps.get("appium:deviceName", "")
        automation = caps.get("appium:automationName", "")
        server = block.get("server_url", "")
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    config._metadata = {
        'Project': 'Isagawa QA Platform (Mobile)',
        'Platform': platform_key,
        'Venue': venue,
        'Device': device_name,
        'Automation Name': automation,
        'Appium Server': server,
        'Report Generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    # Dynamic marker registration - scans test files for @pytest.mark.X
    _register_dynamic_markers(config)


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    """Stash each phase report so driver teardown can tell pass from fail.

    This is the pattern pytest documents for exposing results to fixtures
    (item.stash with a StashKey), not the superseded setattr recipe.
    """
    report = yield
    item.stash.setdefault(_PHASE_REPORT_KEY, {})[report.when] = report
    return report


def pytest_collection_modifyitems(config, items):
    """Deselect items marked for a platform family other than the resolved one.

    Without this, a plain `pytest` run collects every platform's tests and fails
    on the ones that cannot run here. Deselection rather than a skip marker:
    pytest documents both, and deselected items do not fill the report with
    noise that has to be read past. Explicit marker selection (-m ios) is
    unaffected and still composes with this.
    """
    platform_key = config.getoption("--platform")
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            document = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return
    platform_key = platform_key or document.get("default_platform")
    profile = document.get("platforms", {}).get(platform_key, {})
    allowed = set(profile.get("markers", []))
    if not allowed:
        return

    families = {"ios", "android"}
    keep, dropped = [], []
    for item in items:
        owned = {m.name for m in item.iter_markers()} & families
        (dropped if owned and not (owned & allowed) else keep).append(item)

    if dropped:
        config.hook.pytest_deselected(items=dropped)
        items[:] = keep
