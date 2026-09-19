# Reference Implementation

**Purpose:** Canonical code patterns for AI to learn from before generating any layer code.

---

## AI Instructions

**BEFORE generating any Screen Object, Task, Role, or Test code, you MUST read these files:**

| Layer | File to Read | Learn |
|-------|--------------|-------|
| **Screen** | `screens/product_catalog_screen.py` | Platform-keyed locators, atomic methods, state-check methods, return self |
| **Task** | `tasks/shopping_tasks.py` | @autologger, Screen composition, no returns, fluent API |
| **Role** | `roles/shopper.py` | @autologger, Task composition, workflow orchestration |
| **Test** | `tests/test_e2e_browse_and_add_to_cart.py` | AAA pattern, fixtures, Role calls, Screen assertions |

---

## 4-Layer Pattern Summary

### Screen (Screen Object Model)
```python
# NO decorators
# Locators as class constants, keyed by platform
# Atomic methods (one UI action)
# Return self for chaining
# State-check methods for assertions
```

### Task
```python
# @autologger("Task") on methods
# NO decorator on constructor
# Composes Screen Objects
# One domain operation per method
# NO return values
```

### Role
```python
# @autologger("Role") on workflow methods
# @autologger("Role Constructor") on __init__
# Composes Task modules
# Workflow methods call MULTIPLE tasks
# NO return values
```

### Test
```python
# @autologger("Test") decorator
# Call Role workflow methods (chain when workflow requires it)
# Assert via Screen Object state-check methods
# NO test-level orchestration (belongs in Role layer)
```

---

## File Structure

```
_reference/
├── README.md                                   ← You are here
├── __init__.py
├── screens/
│   ├── __init__.py
│   ├── product_catalog_screen.py               ← Screen pattern (catalog)
│   ├── product_detail_screen.py                ← Screen pattern (detail)
│   └── tab_bar_screen.py                       ← Screen pattern (navigation)
├── tasks/
│   ├── __init__.py
│   └── shopping_tasks.py                       ← Task pattern (shopping)
├── roles/
│   ├── __init__.py
│   └── shopper.py                              ← Role pattern (shopper)
└── tests/
    ├── __init__.py
    └── test_e2e_browse_and_add_to_cart.py      ← Test pattern (integration)
```

---

## Key Rules (from patterns)

| Rule | Enforced In |
|------|-------------|
| NO locators in Tasks/Roles | Task, Role |
| NO return values from Tasks/Roles | Task, Role |
| Return `self` from Screen atomic methods | Screen |
| Assert via Screen state-check methods | Test |
| `@autologger` on Task/Role/Test methods | All |
| Locators are platform-keyed dicts, resolved via `locator()` | Screen |
| `MobileInterface` is composed, never inherited | Screen |

---

## What Is Different From The Web

Four things change when the target is a native app rather than a browser.

**There is no URL, so there is no navigate step and no login page.** The app under test is
launched by the session's capabilities, not driven to by address. A Role constructor
therefore takes no `login_url` and no credentials, and the first Task in a flow opens a
tab rather than loading a page.

**A locator is a dict keyed by platform, not a single tuple.** The same screen carries
different element ids on iOS and Android, so each constant maps a platform key to an
`(AppiumBy, value)` pair and `locator()` resolves it against `mobile.platform` at call
time. One test body then runs on both platforms.

**Element ids are discovered, never typed from memory.** Every id in these screens appears
verbatim in a page source committed under [`_captures/`](_captures/) — the same way the
Selenium platform snapshots a page and extracts elements before a Page Object is written.
`/qa-workflow` step 4 performs that discovery against the app under test and builds new
screens from these patterns.

**Only the keys a capture proves are present.** Each constant carries exactly the platform
keys that evidence supports — no more. A key for a platform nobody has looked at is a
guess wearing the costume of a fact, and `locator()` raises rather than falling back, so
the guess would surface as a confusing `NoSuchElement` far from its cause.

The catalog screen is the worked example, because one screen in one product produced four
different cross-platform outcomes:

| Outcome | Handling | Example |
|---|---|---|
| Same id on both | one `"default"` key | `SCREEN_TITLE` — `title` on both |
| Different id, same element | two keys | `SCREEN_ROOT`, `PRODUCT_NAME` (iOS "Name", Android "Title") |
| No counterpart | only the key that exists | `HEADER_TITLE` — Android merges logo and wordmark into one node |
| Two constants, one node | both keys point at it, with a note | `PRODUCT_ITEM` / `PRODUCT_IMAGE` — Android's tile has no id, so the image *is* the tile |

Two keys holding the **same string** is not redundant and does not get collapsed to
`"default"` on sight: `PRODUCT_PRICE` reads `Product Price` on both, but the captures came
from two different builds rather than one cross-platform run, so two keys assert what was
observed and `"default"` would assert more.

**Coverage is partial, and says so.** The Android captures cover browse-and-open, so
`cart_screen.py` and `tab_bar_screen.py` carry no `"android"` key at all and the reference
test stays `@pytest.mark.ios`. The iOS ids are correct but rest on a CI run id rather than
a committed capture — [`_captures/README.md`](_captures/README.md) records that gap
explicitly rather than letting it read as complete.

---

*This is the authoritative source for code patterns. When in doubt, read these files.*
