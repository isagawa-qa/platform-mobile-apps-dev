"""L1/L2 contract suite for tests/conftest.py (backlog 322).

Gates: L1-F1 inventory, L1-F2 workflow_data unchanged, L1-F3 no capability
literals, L1-F4 markers registered, L1-F5 fixture-layer boundary, L2-F2 options
build with no device.

Discipline, from failures recorded in lessons.md:
  * fixture detection is DECORATOR-AWARE via AST, never a grep for "fixture".
  * docstrings excluded - a docstring quoting a rule must not fail that rule.
  * set comparisons run BOTH directions, reporting extras and omissions apart.
  * every check prints its OBSERVED value.
"""
import ast
import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEV = pathlib.Path(__file__).resolve().parent.parent
CONF = DEV / "tests" / "conftest.py"
CONFIG = DEV / "framework" / "resources" / "config" / "environment_config.json"
REFERENCE = DEV / "framework" / "_reference"
SRC = CONF.read_text(encoding="utf-8")
TREE = ast.parse(SRC)

results = []


def record(rule, ok, observed):
    results.append((rule, "PASS" if ok else "FAIL", observed))


def both_ways(label, have, want):
    missing, extra = sorted(want - have), sorted(have - want)
    return (not missing and not extra,
            "%s %d/%d missing=%s extra=%s" % (label, len(have), len(want),
                                              missing or "none", extra or "none"))


def strip_docstring(fn):
    """Statements of fn.body with the docstring removed. Never ast.walk(fn)."""
    stmts = list(fn.body)
    if stmts and isinstance(stmts[0], ast.Expr) and isinstance(stmts[0].value, ast.Constant) \
            and isinstance(stmts[0].value.value, str):
        stmts = stmts[1:]
    return stmts


# ---- L1-F1: inventory, decorator-aware ---------------------------------------
fixtures, hooks, helpers = set(), set(), set()
for node in TREE.body:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        continue
    if any("fixture" in ast.dump(d) for d in node.decorator_list):
        fixtures.add(node.name)
    elif node.name.startswith("pytest_"):
        hooks.add(node.name)
    elif node.name.startswith("_"):
        helpers.add(node.name)

ok_f, obs_f = both_ways("fixtures", fixtures,
                        {"driver", "config", "device", "test_users",
                         "workflow_data", "mobile", "artifacts_dir"})
ok_h, obs_h = both_ways("hooks", hooks,
                        {"pytest_addoption", "pytest_configure",
                         "pytest_html_report_title", "pytest_runtest_makereport",
                         "pytest_collection_modifyitems"})
ok_l, obs_l = both_ways("helpers", helpers,
                        {"_register_dynamic_markers", "_build_options",
                         "_expand_env", "_capture_failure_evidence"})
record("L1-F1", ok_f and ok_h and ok_l, "%s | %s | %s" % (obs_f, obs_h, obs_l))


# ---- L1-F2: workflow_data byte-identical to the template ---------------------
TPL = DEV / "_context" / "tpl_conftest.py"
if TPL.exists():
    tpl_src = TPL.read_text(encoding="utf-8")

    def segment(src, name):
        tree = ast.parse(src)
        for n in tree.body:
            if isinstance(n, ast.FunctionDef) and n.name == name:
                return ast.get_source_segment(src, n)
        return None

    a, b = segment(tpl_src, "workflow_data"), segment(SRC, "workflow_data")
    record("L1-F2", a == b,
           "template=%s chars mobile=%s chars identical=%s"
           % (len(a) if a else None, len(b) if b else None, a == b))
else:
    record("L1-F2", False,
           "template copy absent at %s - cannot compare, so NOT a pass" % TPL)


# ---- L1-F3: no capability VALUE literals -------------------------------------
BANNED_STRINGS = ("iOS", "Android", "XCUITest", "UiAutomator2",
                  "iPhone", "emulator-5554", "http://127.0.0.1:4723")
CAP_NAMES = ("newCommandTimeout", "wdaLaunchTimeout", "simulatorStartupTimeout",
             "wdaStartupRetries", "wdaStartupRetryInterval", "systemPort",
             "wdaLocalPort", "platformVersion", "deviceName")

big_ints, bad_strings, cap_names = [], [], []
for node in TREE.body:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        continue
    for stmt in strip_docstring(node):
        for sub in ast.walk(stmt):
            if isinstance(sub, ast.Constant):
                if isinstance(sub.value, int) and not isinstance(sub.value, bool) \
                        and sub.value > 1000:
                    big_ints.append("%s:%s=%s" % (node.name, sub.lineno, sub.value))
                if isinstance(sub.value, str):
                    for b in BANNED_STRINGS:
                        # the automation-name discriminator is the one sanctioned literal
                        if b in sub.value and node.name != "_build_options":
                            bad_strings.append("%s:%s=%r" % (node.name, sub.lineno, sub.value))
                    for c in CAP_NAMES:
                        if c in sub.value:
                            cap_names.append("%s:%s=%r" % (node.name, sub.lineno, sub.value))

# capability NAMES are permitted in the report-metadata reader; VALUES are not.
cap_names = [c for c in cap_names if not c.startswith("pytest_configure")]
record("L1-F3", not big_ints and not bad_strings and not cap_names,
       "ints>1000=%s banned_strings=%s cap_value_literals=%s"
       % (big_ints or "none", bad_strings or "none", cap_names or "none"))


# ---- L1-F4: markers registered, and the helper is actually CALLED -------------
ini = (DEV / "pytest.ini")
ini_text = ini.read_text(encoding="utf-8") if ini.exists() else ""
declared = {m for m in ("ios", "android", "web")
            if re.search(r"^\s+%s:" % m, ini_text, re.M)}
called = False
for node in TREE.body:
    if isinstance(node, ast.FunctionDef) and node.name == "pytest_configure":
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name) \
                    and sub.func.id == "_register_dynamic_markers":
                called = True
record("L1-F4", declared == {"ios", "android", "web"} and called,
       "declared=%s helper_called_from_pytest_configure=%s"
       % (sorted(declared), called))


# ---- L1-F5: fixture-layer boundary -------------------------------------------
here = [s for s in ("webdriver.Remote", "XCUITestOptions", "UiAutomator2Options")
        if s in SRC]
leaked = []
if REFERENCE.exists():
    for py in REFERENCE.rglob("*.py"):
        text = py.read_text(encoding="utf-8", errors="replace")
        for s in ("webdriver.Remote", "XCUITestOptions", "UiAutomator2Options",
                  "save_screenshot", "page_source"):
            if s in text:
                leaked.append("%s:%s" % (py.relative_to(DEV), s))
record("L1-F5", len(here) == 3 and not leaked,
       "in_conftest=%s leaked_into_reference=%s" % (here, leaked or "none"))


# ---- L2-F2: options build for all four profiles, with no device --------------
sys.path.insert(0, str(DEV / "framework"))
sys.path.insert(0, str(DEV / "tests"))
built, build_errors = {}, []
try:
    import conftest as cf  # noqa: E402

    document = json.loads(CONFIG.read_text(encoding="utf-8"))
    for name, profile in document["platforms"].items():
        venue = cf._expand_env(profile["venue"])
        block = profile.get(venue) or {}
        try:
            options = cf._build_options(cf._expand_env(dict(block)))
            caps = options.to_capabilities()
            forwarded = [k for k in ("server_url", "requires_host_os", "runner",
                                     "credentials") if k in caps]
            built[name] = "%d caps, venue-keys-forwarded=%s" % (
                len(caps), forwarded or "none")
            if forwarded:
                build_errors.append("%s forwarded %s" % (name, forwarded))
        except Exception as exc:  # noqa: BLE001
            build_errors.append("%s: %s" % (name, exc))
except Exception as exc:  # noqa: BLE001
    build_errors.append("import conftest failed: %s" % exc)

record("L2-F2", len(built) == 4 and not build_errors,
       "built=%s errors=%s" % (built or "none", build_errors or "none"))


# ---- report ------------------------------------------------------------------
out = DEV / "_context" / "fixtures-l1-results.txt"
out.parent.mkdir(parents=True, exist_ok=True)
lines = ["%-8s %-4s %s" % (r, v, o) for r, v, o in results]
failed = [r for r, v, _ in results if v == "FAIL"]
lines += ["", "OVERALL: %s  (%d checks, %d failed)"
          % ("PASS" if not failed else "FAIL", len(results), len(failed))]
text = "\n".join(lines)
out.write_text(text + "\n", encoding="utf-8")
print(text)
sys.exit(1 if failed else 0)
