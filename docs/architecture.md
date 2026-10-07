# Architecture

## 5-Layer Architecture

Every test in the Isagawa QA Platform (Mobile) follows a strict separation of concerns. Each layer has one job. The contract itself — the chain, the per-layer rules and the decorator table — is stated once, in [DEVELOPER_GUIDE.md](../DEVELOPER_GUIDE.md#the-5-layer-contract). This page walks through each layer with excerpts of the code this repo actually ships under `framework/`.

| Layer | Responsibility | Example in this repo |
|-------|---------------|---------|
| **Test** | Says what should happen, asserts the result | `test_e2e_browse_and_add_to_cart()` |
| **Role** | Coordinates tasks into a persona's workflow | `Shopper.add_product_to_cart()` |
| **Task** | Performs one domain operation across screens | `ShoppingTasks.open_product()` |
| **Screen Object** | Knows where elements are on one screen, per platform | `ProductCatalogScreen.open_product_at(0)` |
| **MobileInterface** | Wraps the Appium session | `MobileInterface.click_element_at()`, `.wait_for_element_visible()` |

```text
Test (Arrange / Act / Assert)
  └─→ Role (multi-task workflow, user persona)
       └─→ Task (single domain operation)
            └─→ Screen Object (one screen, platform-keyed locators, fluent API)
                 └─→ MobileInterface (Appium session, waits, gestures, contexts)
```

---

## Layer Details

### Layer 1: MobileInterface

The foundation layer, `framework/interfaces/mobile_interface.py`. It wraps one Appium session with:

- Explicit waits from `explicit_wait` in the config (no `time.sleep`)
- Finders that pick an element by position when list items share one accessibility id
- Gestures (`tap`, `swipe`, `long_press`, `scroll_until_visible`, `pinch_open`, `drag_and_drop`) and context switching for hybrid screens (`get_contexts`, `switch_to_webview`, `switch_to_native`)
- App lifecycle: `activate_app`, `terminate_app`, `install_app`, `remove_app`, `query_app_state`
- Logging on every failure, then **re-raising** — the Interface never swallows an error

All device interaction flows through this one class. Screen Objects never call the driver directly. Failure screenshots are deliberately *not* here: `tests/conftest.py` owns failure evidence. Excerpt:

```python
class MobileInterface:
    DEFAULT_EXPLICIT_WAIT = 20

    def click_element_at(self, by: str, value: str, index: int = 0,
                         timeout: Optional[int] = None) -> None:
        elements = self.find_elements(by, value, timeout)
        if index >= len(elements):
            self.logger.error(
                f"Element index out of range: by={by}, value={value}, "
                f"index={index}, found={len(elements)}"
            )
            raise IndexError(
                f"index {index} but only {len(elements)} element(s) match {value!r}"
            )
        try:
            elements[index].click()
        except WebDriverException as exc:
            self.logger.error(
                f"Driver error clicking element at index: by={by}, value={value}, "
                f"index={index}, error={exc}"
            )
            raise
```

Its constructor takes `platform` explicitly (passed by the `mobile` fixture), so every Screen can ask `self.mobile.platform` without touching capabilities.

### Layer 2: Screen Object

Each screen of the app gets one Screen Object class. Excerpt of `framework/_reference/screens/product_catalog_screen.py`:

```python
from appium.webdriver.common.appiumby import AppiumBy
from interfaces.mobile_interface import MobileInterface


class ProductCatalogScreen:

    def __init__(self, mobile: MobileInterface):
        """Compose MobileInterface - NO inheritance."""
        self.mobile = mobile

    SCREEN_ROOT = {
        "ios": (AppiumBy.ACCESSIBILITY_ID, "Catalog-screen"),
        "android": (AppiumBy.ACCESSIBILITY_ID, "Displays all products of catalog"),
    }
    HEADER_TITLE = {"ios": (AppiumBy.ACCESSIBILITY_ID, "AppTitle Icons")}

    def locator(self, name: str):
        entry = getattr(self, name)
        platform = self.mobile.platform
        if platform not in entry:
            raise KeyError(
                f"{type(self).__name__}.{name} has no {platform!r} locator "
                f"(present: {sorted(entry)}). Capture the screen on {platform} "
                f"and add the id - do not reuse another platform's."
            )
        return entry[platform]

    def wait_for_catalog_visible(self, timeout: int = 20) -> "ProductCatalogScreen":
        """Wait for the catalog screen root to be visible."""
        self.mobile.wait_for_element_visible(*self.locator("SCREEN_ROOT"), timeout=timeout)
        return self

    def is_catalog_displayed(self) -> bool:
        """Check the catalog screen is showing."""
        return self.mobile.is_element_displayed(*self.locator("SCREEN_ROOT"))
```

**Key conventions:**
- `__init__` receives `MobileInterface` via composition (no inheritance)
- Locators are class-level constants: a dict mapping a platform key to an `(AppiumBy, value)` pair
- A key exists only where a captured page source proves the id. `HEADER_TITLE` is iOS-only because Android has no such node, and `locator()` raises rather than borrowing another platform's id
- Atomic methods — one UI action each — return `self`; state-checks are `is_*`, `get_*`, `has_*`, `*_count`
- No `@autologger` decorator on Screen methods

**When platforms differ in sequence, not just ids.** iOS reaches the catalog with one tab tap; Android opens a drawer first. A locator cannot add a tap, so `framework/_reference/navigation/` holds one Screen Object per platform with the same method names, and `navigation_for()` picks one when a Task is built. Excerpt of `android_navigation_screen.py`:

```python
class AndroidNavigationScreen:

    MENU_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "View menu")
    MENU_LIST = (AppiumBy.ACCESSIBILITY_ID, "Recycler view for menu")
    CATALOG_ITEM = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Catalog")')

    def open_catalog(self) -> "AndroidNavigationScreen":
        self.mobile.click(*self.MENU_BUTTON)
        self.mobile.wait_for_element_visible(*self.MENU_LIST)
        self.mobile.click(*self.CATALOG_ITEM)
        return self
```

### Layer 3: Task

Tasks perform one domain operation, composing Screen Object calls into fluent chains. Excerpt of `framework/_reference/tasks/shopping_tasks.py`:

```python
class ShoppingTasks:

    def __init__(self, mobile: MobileInterface):
        self.mobile = mobile
        self.catalog_screen = ProductCatalogScreen(mobile)
        self.product_detail_screen = ProductDetailScreen(mobile)
        self.navigation = navigation_for(mobile)
        self.cart_screen = CartScreen(mobile)

    @autologger.automation_logger("Task")
    def open_product(self, index: int = 0) -> None:
        (self.catalog_screen
            .scroll_to_product_item()
            .open_product_at(index))
        (self.product_detail_screen
            .wait_for_detail_visible())
```

**Key conventions:**
- `@autologger.automation_logger("Task")` on every method (not the constructor)
- Composes Screen Objects in `__init__`; the per-platform navigation is resolved once, there
- One domain operation per method; never returns a value; no `try/except`
- There is no navigate-to-URL step: the app is already launched by the session's capabilities

### Layer 4: Role

Roles represent user personas and orchestrate Tasks into complete workflows. Excerpt of `framework/_reference/roles/shopper.py`:

```python
class Shopper:

    @autologger.automation_logger("Role Constructor")
    def __init__(self, mobile_interface: MobileInterface):
        self.mobile = mobile_interface
        self.shopping_tasks = ShoppingTasks(mobile_interface)

    @autologger.automation_logger("Role")
    def add_product_to_cart(self, index: int = 0, quantity: int = 1) -> None:
        self.shopping_tasks.open_catalog()
        self.shopping_tasks.open_product(index)
        self.shopping_tasks.add_product_to_cart(quantity)
```

**Key conventions:**
- `"Role Constructor"` on `__init__`, `"Role"` on workflow methods; each workflow calls several Tasks
- The constructor takes no URL and no credentials: a native app is launched, not navigated to. A login-skipping `_continue` variant has no counterpart because this flow has no login step
- Never returns values

### Layer 5: Test

Tests are thin — they call Role workflow methods per phase and assert via Screen state-checks. Excerpt of `framework/_reference/tests/test_e2e_browse_and_add_to_cart.py`:

```python
class TestE2EBrowseAndAddToCart:

    @pytest.fixture(autouse=True)
    def setup(self, mobile, device, test_users):
        self.mobile = mobile
        self.catalog_screen = ProductCatalogScreen(self.mobile)
        self.product_detail_screen = ProductDetailScreen(self.mobile)
        self.cart_screen = CartScreen(self.mobile)

    @pytest.mark.ios
    @autologger.automation_logger("Test")
    def test_e2e_browse_and_add_to_cart(self):
        shopper = Shopper(self.mobile)
        product_index = 0
        quantity = 2

        shopper.add_product_to_cart(product_index, quantity)

        assert self.product_detail_screen.is_add_to_cart_available(), \
            "expected the product detail screen to offer Add To Cart"

        shopper.review_cart()

        assert not self.cart_screen.is_empty(), \
            "expected the cart to hold the product that was just added"
```

**Key conventions:**
- `@autologger.automation_logger("Test")` plus a platform marker (`ios`, `android`, `web`)
- AAA pattern; one Role workflow call per phase; each phase is asserted on a *different* screen
- Fixtures come from `tests/conftest.py`: `mobile`, `device`, `test_users`, `workflow_data`
- Causal dependency: the product opened in phase 1 is the one the cart must hold in phase 2

---

## Why 5 Layers?

```text
Test: test_e2e_browse_and_add_to_cart()
├─ Phase 1: Shopper.add_product_to_cart()           ← Role
│   ├─ ShoppingTasks.open_catalog()                  ← Task
│   │   └─ Navigation: drawer or tab → Catalog       ← Screen → MobileInterface
│   ├─ ShoppingTasks.open_product()                  ← Task
│   │   └─ ProductCatalogScreen: scroll → open tile  ← Screen → MobileInterface
│   └─ ShoppingTasks.add_product_to_cart()           ← Task
├─ Assert: detail screen offers Add To Cart
├─ Phase 2: Shopper.review_cart()                    ← Role
│   └─ ShoppingTasks.open_cart()                     ← Task
└─ Assert: cart displayed, not empty, has total
```

Remove any layer and the architecture degrades:
- **Remove Roles** → Tests orchestrate tasks directly (duplication across tests)
- **Remove Tasks** → Screen calls scatter across Roles (every tap inline in every workflow)
- **Remove Screen Objects** → Locators and driver calls leak into Tasks, and every Task branches on platform
- **Remove MobileInterface** → Waits, logging and re-raise duplicated in every Screen

---

## Decorator Strategy

The `@autologger.automation_logger` decorator (`framework/resources/utilities/autologger.py`) traces the run layer by layer in the terminal: which Role called which Task. The decorator table is part of the contract in [DEVELOPER_GUIDE.md](../DEVELOPER_GUIDE.md#the-5-layer-contract); Screens carry none.

---

## Data Flow

```text
environment_config.json + .env + tests/data + tests/{workflow}/data
  ↓
conftest: device (platform → device location → capabilities) → driver → mobile
  ↓
Test → Role → Task → Screen Object (platform-keyed locator → (AppiumBy, value))
  ↓
MobileInterface → Appium server → simulator, emulator or device
```

**Assertions flow upward:** Tests assert by calling Screen state-check methods. Tasks and Roles never return values.

---

## Coverage

What this architecture runs on today, and what is blocked, is in [PLATFORM_GUIDE.md](../PLATFORM_GUIDE.md#what-runs-today). In short: the iOS reference flow runs on a **simulator** (the free GitHub `macos-15` runner, or reached from Windows through the `ios-tunnel` workflow); iOS real devices (`L3-03`), iOS hybrid (`L3-04`) and iOS mobile web (`L3-05`) are **BLOCKED with their gates OPEN**.

---

## Reference Implementations

Browse `framework/_reference/` for the canonical patterns; [`framework/_reference/README.md`](../framework/_reference/README.md) says which file to read per layer.

| Layer | File |
|-------|------|
| **Screen** | `screens/product_catalog_screen.py`, `screens/product_detail_screen.py`, `screens/cart_screen.py` |
| **Screen (per platform)** | `navigation/ios_navigation_screen.py`, `navigation/android_navigation_screen.py` |
| **Task** | `tasks/shopping_tasks.py` |
| **Role** | `roles/shopper.py` |
| **Test** | `tests/test_e2e_browse_and_add_to_cart.py` |
| **Evidence** | `_captures/*.xml` — the page sources every id was read from |

These are the authoritative source. When in doubt, read the reference implementations.
