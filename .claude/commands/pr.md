---
description: Instant PR review - validates code against framework patterns like a senior SDET would
---

# /pr - Instant Code Review

What takes 30-60 min in a PR cycle, done in 5 seconds.

---

## Instructions

### 1. Scan Directories

Scan all framework layers:
- `framework/screens/` - Screen Objects
- `framework/tasks/` - Task modules
- `framework/roles/` - Role modules
- `tests/` - Test files (exclude conftest.py, __init__.py)

`framework/_reference/` is the teaching set. Review it only when it changed.

### 2. Layer Architecture Checks

#### Screen Layer (`framework/screens/**/*.py`)
- [x] Has locators as class constants (platform-keyed dicts of `(AppiumBy.*, value)`)
- [x] Has a `locator(self, name)` resolver
- [x] Has atomic methods returning `self`
- [x] Has state-check methods (`is_*`, `get_*`, `has_*`, `*_count`)
- [ ] VIOLATION: Has `@autologger` decorator (Screens don't use it)
- [ ] VIOLATION: Imports from tasks/ or roles/
- [ ] VIOLATION: Reaches the driver directly (`self.mobile.driver`, raw WebElement calls)
- [ ] VIOLATION: A platform key with no corresponding capture
- [ ] VIOLATION: A `"default"` key asserted from a single platform's capture

#### Task Layer (`framework/tasks/**/*.py`)
- [x] Has `@autologger.automation_logger("Task")` decorator on methods
- [x] NO decorator on `__init__`
- [x] Methods return `None` (no return statements with values)
- [x] Imports from screens/ only
- [ ] VIOLATION: Contains `AppiumBy.` imports or locator tuples
- [ ] VIOLATION: Imports from roles/
- [ ] VIOLATION: Contains try/except

#### Role Layer (`framework/roles/**/*.py`)
- [x] Has `@autologger.automation_logger("Role Constructor")` on `__init__`
- [x] Has `@autologger.automation_logger("Role")` on workflow methods
- [x] Workflow methods call MULTIPLE tasks
- [x] Methods return `None` (no return statements with values)
- [x] Imports from tasks/ only
- [ ] VIOLATION: Contains `AppiumBy.` imports or locator tuples
- [ ] VIOLATION: Imports from screens/ directly
- [ ] VIOLATION: Contains try/except

#### Test Layer (`tests/**/*.py`)
- [x] Has `@autologger.automation_logger("Test")` decorator
- [x] Has a platform marker (`@pytest.mark.ios` / `.android` / `.web`)
- [x] Imports Role from roles/
- [x] Imports Screen from screens/ (for assertions only)
- [x] Uses Screen state-check methods in assertions
- [ ] VIOLATION: Contains `AppiumBy.` imports or locator tuples
- [ ] VIOLATION: Imports from tasks/ directly
- [ ] VIOLATION: Sets capabilities or builds a driver (that is conftest's job)
- [ ] VIOLATION: Test does orchestration that belongs in Role layer (chaining multiple Role methods is OK when workflow requires it — e.g., capturing intermediate state between steps)

### 3. Senior SDET Quality Checks

#### Evidence (mobile-specific, CRITICAL)
- [ ] VIOLATION: A locator value that appears in no capture under `tests/_state/captures/`
- [ ] VIOLATION: A locator changed without a capture citation in the commit

#### Code Quality (Any violation triggers HITL)
- [ ] VIOLATION: `time.sleep()` calls - use MobileInterface wait methods instead
- [ ] VIOLATION: Hardcoded credentials - use config/fixtures (unless user specifies otherwise)
- [ ] VIOLATION: Magic numbers without explanation - use constants or inline comments (e.g., `timeout=30` needs `# 30s for a cold WDA launch`)
- [ ] VIOLATION: Missing docstrings - all methods require docstrings (see `framework/_reference/`)
- [ ] VIOLATION: Complex logic without inline comments explaining why

#### Naming Conventions
- [ ] VIOLATION: Methods not snake_case
- [ ] VIOLATION: Classes not PascalCase
- [ ] VIOLATION: Locator constants not SCREAMING_SNAKE_CASE

#### Test Quality
- [ ] VIOLATION: Test without assertions
- [ ] VIOLATION: Test depends on another test's state
- [ ] VIOLATION: Bare `except:` without specific exception

#### Wait Patterns
- [ ] VIOLATION: Implicit waits mixed with explicit waits
- [ ] VIOLATION: No timeout parameter on wait calls

#### MobileInterface Usage
- [ ] VIOLATION: Wrapping MobileInterface methods instead of calling directly
- [ ] VIOLATION: Creating new wait/tap/type methods when MobileInterface already has them
- [ ] NOTE: If a needed method doesn't exist in MobileInterface, trigger HITL to discuss adding it

---

## CRITICAL: HITL Protocol

**On ANY violation found, you MUST follow this protocol:**

### Rule: STOP on Violation

When violations are found:
1. **STOP** - Do not attempt autonomous fixes
2. **REPORT** - Show violations with file:line references
3. **WAIT** - Get human decision before proceeding

### What NOT To Do

- Do NOT auto-fix violations without asking
- Do NOT assume you know the right fix
- Do NOT skip violations and continue
- Do NOT loop trying different fixes

---

## Report Format

### If All Pass:
```
PR REVIEW: APPROVED
============================

PASS: framework/screens/catalog/product_catalog_screen.py
PASS: framework/tasks/catalog/catalog_tasks.py
PASS: framework/roles/catalog/shopper.py
PASS: tests/catalog/test_browse_catalog.py

Summary: 4 files checked, 0 violations

Ready to merge.
```

### If Violations Found (HITL Triggered):
```
PR REVIEW: CHANGES REQUESTED
============================

PASS: framework/screens/catalog/product_catalog_screen.py
PASS: framework/roles/catalog/shopper.py
FAIL: framework/tasks/catalog/catalog_tasks.py
  - Line 9: VIOLATION - Has `from appium.webdriver.common.appiumby import AppiumBy`
  - Line 84: VIOLATION - Uses an ACCESSIBILITY_ID locator in the Task layer
FAIL: tests/catalog/test_browse_catalog.py
  - Line 23: VIOLATION - `time.sleep(5)` - use an explicit wait

Summary: 4 files checked, 2 failed, 3 violations

==========================================

HOW SHOULD WE PROCEED?

1. Fix All
   -> AI fixes each violation
   -> Re-runs /pr after fixes

2. Fix Specific
   -> You specify which violations to fix
   -> AI applies only those fixes

3. Explain
   -> AI explains why each is a violation
   -> You decide what to do

4. Ignore + Approve
   -> Skip these violations (document reason)
   -> Proceed anyway

5. Other
   -> Describe what you want to do

Enter choice (1-5):
```

---

## HITL Response Protocol

When violations are found:

1. **Present violations clearly**
   - File path and line number
   - Violation type and rule
   - Brief explanation

2. **Present numbered options (1-5)**
   - Always include all 5 options
   - Wait for user input

3. **Handle user decision**
   - Option 1 (Fix All): Fix each violation, re-run /pr
   - Option 2 (Fix Specific): Ask which ones, fix only those
   - Option 3 (Explain): Explain each violation's impact
   - Option 4 (Ignore): Document reason, mark as approved with exceptions
   - Option 5 (Other): Follow user's instructions

4. **After fixes applied**
   - Re-run /pr to verify
   - Report new results
   - Repeat until clean or user approves

**Key Rule:** AI must NOT fix without user decision. Present options, wait for input.

**An evidence violation is never eligible for Option 4.** A locator with no
capture behind it is not a style preference; it is a claim nobody checked.

---

## Severity Levels

| Severity | Description | Examples |
|----------|-------------|----------|
| **CRITICAL** | Breaks architecture or invents evidence | Locators in Task, Role imports screens, untraceable locator |
| **HIGH** | Best practice violation | time.sleep(), hardcoded creds, driver call above the Interface |
| **MEDIUM** | Code quality issue | Missing docstring, naming convention |
| **LOW** | Style/preference | Minor formatting |

Report violations grouped by severity, CRITICAL first.
