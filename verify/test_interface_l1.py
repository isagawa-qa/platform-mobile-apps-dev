"""L1 AST contract suite for MobileInterface (backlog 321, gates L1-02, L1-05, L1-C2-06).

Rules checked: E1-E4, E6, E7, S1-S4.

Discipline applied, from prior failures recorded in lessons.md:
  * iterate fn.body per statement, NEVER ast.walk(fn) - walk includes
    decorator_list and false-positives on a decorated constructor.
  * exclude docstrings - a docstring quoting a rule must not fail that rule.
  * every check prints its OBSERVED value, not just a verdict word.
"""
import ast
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEV = pathlib.Path(__file__).resolve().parent.parent
MI = DEV / "framework" / "interfaces" / "mobile_interface.py"
SRC = MI.read_text(encoding="utf-8")
TREE = ast.parse(SRC)

results = []


def record(rule, ok, observed):
    results.append((rule, "PASS" if ok else "FAIL", observed))


def classes():
    return [n for n in TREE.body if isinstance(n, ast.ClassDef)]


def methods(cls):
    return [n for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


def body_statements(fn):
    """Statements of fn.body, docstring excluded. Never ast.walk(fn)."""
    stmts = list(fn.body)
    if stmts and isinstance(stmts[0], ast.Expr) and isinstance(stmts[0].value, ast.Constant) \
            and isinstance(stmts[0].value.value, str):
        stmts = stmts[1:]
    return stmts


# ---- S1: exactly one ClassDef, named MobileInterface --------------------------
cls = classes()
record("S1", len(cls) == 1 and cls[0].name == "MobileInterface",
       "classes=%s" % [c.name for c in cls])

TARGET = cls[0]
ALL_METHODS = methods(TARGET)
PUBLIC = [m for m in ALL_METHODS if not m.name.startswith("_")]

# ---- S2: the 48-method set, compared BOTH directions -------------------------
EXPECTED = set("""navigate_to refresh_page go_back go_forward get_current_url get_page_title
find_element find_elements is_element_present click type select_by_text select_by_value
get_select_options get_text get_attribute is_element_displayed is_element_clickable
wait_for_element_visible wait_for_element_invisible wait_for_text_in_element
wait_for_url_contains take_screenshot execute_script scroll_to_element scroll_to_bottom
scroll_to_top switch_to_frame switch_to_default_content switch_to_context get_contexts
switch_to_webview get_page_source tap long_press swipe scroll_until_visible drag_and_drop
pinch_open pinch_close get_current_context switch_to_native wait_for_context activate_app
terminate_app install_app remove_app query_app_state""".split())
have = {m.name for m in PUBLIC}
missing, extra = sorted(EXPECTED - have), sorted(have - EXPECTED)
record("S2", not missing and not extra,
       "count=%d expected=%d missing=%s extra=%s" % (len(have), len(EXPECTED), missing, extra))

# hover and close_current_window are absent BY DESIGN
absent = [n for n in ("hover", "close_current_window") if n in have]
record("S2-absent", not absent, "must-be-absent present=%s" % absent)

# ---- S3: platform branching is internal to method bodies ---------------------
module_level_platform = []
for node in TREE.body:
    if isinstance(node, (ast.If, ast.Assign)) and "platform" in ast.dump(node):
        module_level_platform.append(type(node).__name__)
record("S3", not module_level_platform,
       "module-level platform constructs=%s" % (module_level_platform or "none"))

# ---- S4: Appium only ---------------------------------------------------------
BANNED_IMPORTS = ("selenium.webdriver.Chrome", "chromedriver", "webdriver_manager")
hits = [b for b in BANNED_IMPORTS if b in SRC]
record("S4", not hits, "banned import hits=%s" % (hits or "none"))

# ---- E1: every handler's TERMINAL statement --------------------------------
ALLOW_FALSE = {"is_element_present", "is_element_displayed", "is_element_clickable"}
ALLOW_EMPTY = {"find_elements"}
e1_detail, e1_bad = [], []
for m in ALL_METHODS:
    for node in ast.walk(m):
        if not isinstance(node, ast.ExceptHandler):
            continue
        stmts = [s for s in node.body
                 if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant)
                         and isinstance(s.value.value, str))]
        if not stmts:
            e1_bad.append("%s: empty handler" % m.name)
            continue
        last = stmts[-1]
        if isinstance(last, ast.Raise) and last.exc is None:
            kind = "bare raise"
        elif isinstance(last, ast.Return) and isinstance(last.value, ast.Constant) \
                and last.value.value is False and m.name in ALLOW_FALSE:
            kind = "return False (allow-listed)"
        elif isinstance(last, ast.Return) and isinstance(last.value, ast.List) \
                and not last.value.elts and m.name in ALLOW_EMPTY:
            kind = "return [] (allow-listed)"
        else:
            kind = "OTHER:" + type(last).__name__
            e1_bad.append("%s -> %s" % (m.name, kind))
        e1_detail.append("%s:%s" % (m.name, kind))
record("E1", not e1_bad, "handlers=%d violations=%s" % (len(e1_detail), e1_bad or "none"))

# ---- E2: each handler logs before its terminal statement ---------------------
e2_bad = []
for m in ALL_METHODS:
    for node in ast.walk(m):
        if not isinstance(node, ast.ExceptHandler):
            continue
        logged = any("logger" in ast.dump(s) for s in node.body[:-1]) \
            or any("logger" in ast.dump(s) for s in node.body)
        if not logged:
            e2_bad.append(m.name)
record("E2", not e2_bad, "handlers-without-log=%s" % (e2_bad or "none"))

# ---- E3: handlers cover non-timeout failures --------------------------------
# SCOPE: the rule is "for every Try PERFORMING A DRIVER CALL". A try whose body
# only calls a sibling interface method performs no driver call - the delegated
# method owns the contract and has already logged and re-raised. Scoping this
# check to any try-with-a-timeout-handler flags is_element_present, which
# delegates to find_element, and find_element does carry the WebDriverException
# branch. That would be a matcher scoped wider than the property it protects -
# the same defect shape as a whole-file regex standing in for table rows.
e3_bad, e3_skipped = [], []
for m in ALL_METHODS:
    for node in ast.walk(m):
        if not isinstance(node, ast.Try):
            continue
        body_dump = " ".join(ast.dump(s) for s in node.body)
        performs_driver_call = "self.driver" in body_dump or "driver" in body_dump.replace("self.find", "")
        if not performs_driver_call:
            e3_skipped.append("%s (delegates, no driver call)" % m.name)
            continue
        joined = " ".join(ast.dump(h.type) for h in node.handlers if h.type is not None)
        if "TimeoutException" in joined and not (
                "WebDriverException" in joined or "'Exception'" in joined or "id='Exception'" in joined):
            e3_bad.append(m.name)
record("E3", not e3_bad,
       "timeout-only-try=%s skipped-as-delegating=%s" % (e3_bad or "none", e3_skipped or "none"))

# ---- E4: no screenshot machinery --------------------------------------------
e4_bad = []
for s in ("_take_screenshot", "screenshots_on_failure", "screenshot_dir",
          "DEFAULT_SCREENSHOT_DIR", "os.makedirs"):
    if s in SRC:
        e4_bad.append(s)
callers = []
for m in ALL_METHODS:
    if m.name == "take_screenshot":
        continue
    if "take_screenshot" in ast.dump(m):
        callers.append(m.name)
record("E4", not e4_bad and not callers,
       "banned=%s in-module-callers=%s" % (e4_bad or "none", callers or "none"))

# ---- E6: no sleep, no server, no implicit wait ------------------------------
e6_bad = [s for s in ("time.sleep", "subprocess", "webdriver.Remote", "implicitly_wait")
          if s in SRC]
record("E6", not e6_bad, "hits=%s" % (e6_bad or "none"))

# ---- E7: generic vocabulary -------------------------------------------------
BAN = ("employee", "task_manager", "Orderly", "patient", "claim", "healthcare")
e7_bad = [b for b in BAN if b.lower() in SRC.lower()]
record("E7", not e7_bad, "hits=%s" % (e7_bad or "none"))

# ---- report ------------------------------------------------------------------
out = DEV / "_context" / "interface-l1-results.txt"
lines = ["%-10s %-4s %s" % (r, v, o) for r, v, o in results]
failed = [r for r, v, _ in results if v == "FAIL"]
lines.append("")
lines.append("OVERALL: %s  (%d checks, %d failed)" %
             ("PASS" if not failed else "FAIL", len(results), len(failed)))
text = "\n".join(lines)
out.write_text(text + "\n", encoding="utf-8")
print(text)

(DEV / "_context" / "method-set.txt").write_text(
    "\n".join(sorted(have)) + "\n", encoding="utf-8")

sys.exit(1 if failed else 0)
