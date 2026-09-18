"""L2-04: the config resolves to a device profile (backlog 322).

This is a REAL pytest test file, deliberately not a --collect-only run.
Collection never instantiates a fixture, so it can never reach the pytest.fail
calls these rules exist to trigger - a collection run would pass while proving
nothing.

Cases 1 and 3 request the `device` fixture directly. Cases 2 and 4 assert a
FAILURE, so they run pytest in a subprocess and assert the run went red with the
expected message: an assertion about a failure is worthless unless the failure
is observed.

No device and no Appium server is required. Resolution is config-only.
"""
import json
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG = ROOT / "framework" / "resources" / "config" / "environment_config.json"
DOCUMENT = json.loads(CONFIG.read_text(encoding="utf-8"))


def _run_pytest(args, env_overrides=None):
    """Run this file's probe test in a subprocess and return (rc, output)."""
    import os
    env = dict(os.environ)
    env.pop("PLATFORM", None)
    if env_overrides:
        env.update(env_overrides)
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", str(pathlib.Path(__file__)),
         "-k", "probe", "-p", "no:cacheprovider", "--no-header", "-q", *args],
        cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=180,
    )
    return proc.returncode, proc.stdout + proc.stderr


def test_probe_device_resolves(device):
    """Support test driven by the subprocess cases. Not a case itself."""
    assert device["platformKey"]


# ---------------------------------------------------------------- case 1
def test_known_platform_resolves_to_expected_profile(device, request):
    """A known --platform resolves to that profile's venue block."""
    requested = request.config.getoption("--platform") or DOCUMENT["default_platform"]
    assert device["platformKey"] == requested, (
        f"requested {requested!r} but resolved {device['platformKey']!r}")
    assert "server_url" in device, f"resolved block has no server_url: {sorted(device)}"
    assert "capabilities" in device, f"resolved block has no capabilities: {sorted(device)}"
    caps = device["capabilities"]
    assert "platformName" in caps and "appium:automationName" in caps, (
        f"capabilities missing the two required keys: {sorted(caps)}")
    print(f"\n  case 1 observed: platformKey={device['platformKey']!r} "
          f"venue={device.get('venue')!r} caps={len(caps)}")


# ---------------------------------------------------------------- case 3
def test_omitted_platform_uses_config_default(device):
    """Omitting --platform resolves to config['default_platform']."""
    expected = DOCUMENT["default_platform"]
    assert device["platformKey"] == expected, (
        f"default_platform is {expected!r} but resolved {device['platformKey']!r}")
    print(f"\n  case 3 observed: default_platform={expected!r} resolved to "
          f"{device['platformKey']!r}")


# ---------------------------------------------------------------- case 2
def test_unknown_platform_fails_naming_the_config_path():
    """An unknown --platform must FAIL, and the message must name the config."""
    rc, out = _run_pytest(["--platform", "definitely-not-a-profile"])
    assert rc != 0, f"expected a red run for an unknown platform, got rc=0\n{out}"
    assert "is not a key of platforms" in out, (
        f"failure message did not explain the problem:\n{out[-2000:]}")
    assert "environment_config.json" in out, (
        f"failure message did not name the config path:\n{out[-2000:]}")
    print(f"\n  case 2 observed: rc={rc}, message names the config path")


# ---------------------------------------------------------------- case 4
def test_missing_variable_fails_naming_the_variable_and_env():
    """A ${VAR} with no value and no default must FAIL naming it and .env.

    Driven by pointing a venue at a profile whose block carries a bare ${VAR}.
    If every block in the shipped config has defaults, the case says so rather
    than silently passing - an assertion that cannot fire is not evidence.
    """
    bare = []
    for name, profile in DOCUMENT["platforms"].items():
        for venue in ("local", "ci", "remote", "cloud"):
            block = profile.get(venue) or {}
            for key, value in {**block, **block.get("capabilities", {})}.items():
                if isinstance(value, str) and value.startswith("${") \
                        and ":-" not in value and value.endswith("}"):
                    bare.append((name, venue, key, value))
    if not bare:
        pytest.skip("no bare ${VAR} without a default exists in the shipped "
                    "config, so this case has nothing to trigger")

    name, venue, key, value = bare[0]
    var = value[2:-1]
    rc, out = _run_pytest(["--platform", name],
                          {f"MOBILE_VENUE_{DOCUMENT['platforms'][name]['family'].upper()}": venue})
    assert rc != 0, f"expected a red run for unset {var}, got rc=0\n{out}"
    assert var in out, f"failure did not name the variable {var}:\n{out[-2000:]}"
    assert ".env" in out, f"failure did not name .env:\n{out[-2000:]}"
    print(f"\n  case 4 observed: rc={rc}, {var} and .env both named "
          f"(from {name}.{venue}.{key})")
