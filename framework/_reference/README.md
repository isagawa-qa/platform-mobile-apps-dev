# Reference Implementation

**Purpose:** Canonical code patterns for AI to learn from before generating any layer code.

---

## AI Instructions

**BEFORE generating any Screen Object, Task, Role, or Test code, you MUST read these files:**

| Layer | File to Read | Learn |
|-------|--------------|-------|
| **Screen** | `screens/product_catalog_screen.py` | Platform-keyed locators, atomic methods, state-check methods, return self |
| **Screen (per-platform)** | `navigation/android_navigation_screen.py` | When platforms differ in SEQUENCE, not just ids — and why that belongs here |
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
├── _captures/                                  ← The evidence. Every id below is in here
│   ├── README.md
│   ├── android-catalog.xml
│   ├── android-product-detail.xml
│   ├── android-cart.xml
│   ├── android-cart-empty.xml
│   └── android-menu.xml
├── screens/                                    ← SHARED across platforms
│   ├── __init__.py
│   ├── product_catalog_screen.py               ← Screen pattern (catalog)
│   ├── product_detail_screen.py                ← Screen pattern (detail)
│   └── cart_screen.py                          ← Screen pattern (cart)
├── navigation/                                 ← PER-PLATFORM. The one real divergence
│   ├── __init__.py                             ← navigation_for(): resolves once
│   ├── ios_navigation_screen.py                ← tab bar. Catalog = 1 tap
│   └── android_navigation_screen.py            ← header + drawer. Catalog = 2 taps
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

**Why `navigation/` is split and `screens/` is not.** The three screens are the
same on both platforms — same elements, same order, different ids — so each is one
class with a platform-keyed locator per constant. Navigation is not. iOS carries a
persistent bottom tab bar, so reaching the catalog is one tap; Android puts the
catalog inside a drawer behind a hamburger, so it is two. That is a difference in
the **sequence of actions**, and `locator()` only swaps ids — it cannot make a
method perform an extra tap.

So the divergence is absorbed in the Screen layer, which is what that layer is for.
`navigation_for()` picks the class once, when a Task is constructed, and is the only
place in this reference that reads `mobile.platform` to decide behaviour. No Task,
Role or Test branches on platform. Both classes expose the same method names, so
`open_catalog()` reads identically either way.

These are Screen Objects like any other — the `Screen` suffix marks the layer of the
contract, not a claim to occupy the whole viewport. They model persistent chrome, the
mobile counterpart of a Page Object for a site header.

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
| Different id, same element | two keys | `SCREEN_ROOT`, `PRODUCT_NAME` (iOS "Name", Android "Title") |
| Same id on both | **still** two keys | `SCREEN_TITLE`, `PRODUCT_PRICE` — identical strings, written twice |
| No counterpart | only the key that exists | `HEADER_TITLE` — Android merges logo and wordmark into one node |
| Two constants, one node | both keys point at it, with a note | `PRODUCT_ITEM` / `PRODUCT_IMAGE` — Android's tile has no id, so the image *is* the tile |

**There is no `"default"` key and no fallback of any kind.** A key means "this id was
observed on THIS platform", so one key cannot speak for a platform nobody captured — and
the config defines four (`ios`, `android`, `ios-web`, `android-web`). Two keys holding an
identical string are not redundant; they are two observations that happen to agree.

`CartScreen.EMPTY_MESSAGE` is why this matters rather than being pedantry. Both platforms
render the same words, "No Items" — yet iOS exposes that string as the accessibility id
while Android exposes it only as visible text, so the two need different *strategies*, not
just different values. Matching text is not a shared locator, and a single key cannot tell
the two cases apart.

**Coverage is stated, not implied.** All three shared screens now carry both key sets,
captured live. The iOS ids are correct but rest on a CI run id rather than a committed
capture — [`_captures/README.md`](_captures/README.md) records that gap explicitly rather
than letting it read as complete.

**Capture the state you assert, not just the state you pass through.** `EMPTY_MESSAGE`
needed its own capture (`android-cart-empty.xml`): a populated cart cannot prove what an
empty one shows, and that locator is read precisely when the cart is empty. Capturing only
the happy path would have left the one locator that matters unevidenced.

---

*This is the authoritative source for code patterns. When in doubt, read these files.*
