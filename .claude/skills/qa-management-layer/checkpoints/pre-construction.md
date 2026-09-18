# Pre-Construction Checkpoint

**Invoke:** Before writing ANY code in Step 4 (Construction Phase)

---

## MANDATORY: Complete Before Writing Code

### 0. Reuse Check — MANDATORY SCAN (ALL THREE LAYERS)

**⛔ BLOCKING: Scan screens, tasks, AND roles. Show output. Check for duplicates.**

```
ACTION REQUIRED — RUN ALL THREE COMMANDS:

1. find framework/screens -name "*.py" -not -name "__init__.py"
2. find framework/tasks   -name "*.py" -not -name "__init__.py"
3. find framework/roles   -name "*.py" -not -name "__init__.py"

SHOW all output. CHECK each layer for duplicates.
```

**Duplicate = same filename in different workflows:**
- `framework/screens/workflow_A/tab_bar_screen.py` + `framework/screens/workflow_B/tab_bar_screen.py` → DUPLICATE
- `framework/tasks/workflow_A/auth_tasks.py` + `framework/tasks/workflow_B/auth_tasks.py` → DUPLICATE

**When ANY duplicate found in ANY layer, STOP and ask:**

```
DUPLICATES DETECTED
===================

SCREENS:
  tab_bar_screen.py exists in:
    → framework/screens/catalog/tab_bar_screen.py
    → framework/screens/checkout/tab_bar_screen.py

TASKS:
  (check for duplicates)

ROLES:
  (check for duplicates)

OPTIONS:
1. CONSOLIDATE NOW - Move ALL duplicates to common/, update imports
2. CONTINUE - Proceed, consolidate later (adds technical debt)

Which option?
```

**Generic modules (consolidate to common/):**
- Screens: TabBarScreen, LoginScreen, NavigationDrawerScreen, SearchScreen
- Tasks: AuthTasks, NavigationTasks (sign in / sign out flows)
- Roles: Shared authentication roles

**Workflow-specific (keep separate):** ProductCatalogScreen, CheckoutInfoScreen, domain-unique modules

---

### 1. Read Lessons Learned FIRST

**⛔ BEFORE writing ANY code, read lessons.md:**

```
.claude/lessons/lessons.md
```

This file is created by `/kernel/domain-setup` step 8. If the repo has not been
through domain-setup yet, it will not exist — note that and continue. Once it
exists, reading it is mandatory.

**Extract and APPLY all lessons to your code:**
- Wait patterns (wait before tap, wait before assert)
- Locator patterns that proved stable on each platform
- Anti-patterns to avoid
- Quality gates that were added

**DO NOT repeat mistakes that are already documented.**

---

### 2. Read Reference Files

You MUST read these files NOW (not from memory):

```
framework/_reference/screens/*.py → Screen Object patterns
framework/_reference/tasks/*.py   → Task patterns
framework/_reference/roles/*.py   → Role patterns
framework/_reference/tests/*.py   → Test patterns
framework/_reference/README.md    → What differs from the web
```

**Read each file. Extract patterns. Apply to your code.**

### 3. Check MobileInterface Methods

Before writing ANY interaction logic:

1. **READ** `framework/interfaces/mobile_interface.py`
2. **LIST** methods available (click, type, tap, swipe, wait, context…)
3. **USE** existing methods - do not create workarounds

### 4. Confirm Every Locator Has Evidence

```
FOR EACH locator you are about to write:
  grep its literal value against tests/_state/captures/*.xml
```

**If the value is not found, you invented it. Do not write it.** Go back and
capture the screen. An id that cannot be traced to a dump was reasoned about,
not observed.

### 5. Forbidden Patterns

Do NOT use these in generated code:

```python
# FORBIDDEN in Screen Objects:
import time
time.sleep(...)             # Use MobileInterface wait methods

self.mobile.driver.find_element(...)   # Never reach past the Interface

# FORBIDDEN in Tasks:
from appium.webdriver.common.appiumby import AppiumBy
AppiumBy.ACCESSIBILITY_ID, etc.        # Locators belong in Screens only

# FORBIDDEN everywhere:
try:
    ...
except:                     # Never bare except
    pass
```

### 6. Layer Rules Reminder

| Layer | Returns | Contains |
|-------|---------|----------|
| Screen | `self` | Platform-keyed locators, `locator()`, atomic methods, state-check methods |
| Task | `None` | Workflow orchestration, @autologger decorator |
| Role | `None` | Multi-task workflows, @autologger decorator |
| Test | N/A | Role workflow calls (no test-level orchestration), assertions via Screen state methods |

---

## Confirmation

**You MUST confirm each item was DONE (not just understood):**

- [ ] I RAN `find` on all 3 layers and SHOWED output
- [ ] I CHECKED for duplicate filenames, PRESENTED HITL if found
- [ ] I READ lessons.md and will APPLY all lessons to my code
- [ ] I READ reference files (not from memory)
- [ ] I CHECKED MobileInterface methods
- [ ] I GREPPED every locator value against the captures

**If you skipped lessons.md, GO BACK AND READ IT.**
**If any locator failed the grep, GO BACK AND CAPTURE.**

**Now proceed with code generation.**
