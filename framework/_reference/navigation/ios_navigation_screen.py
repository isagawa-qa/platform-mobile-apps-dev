"""
IOSNavigationScreen - Screen Object Model (iOS only)

Screen Object for the iOS bottom tab bar. Handles moving between the
catalog, the cart and the menu.

Like every Screen Object here it is the SCREEN layer of the contract
Test -> Role -> Task -> Screen -> Interface. It models a persistent
component rather than a whole screen - the tab bar is chrome that outlives
the content above it - which is the mobile equivalent of a Page Object that
models a site header. The `Screen` suffix marks the layer, not a claim to
own the viewport.
"""

from appium.webdriver.common.appiumby import AppiumBy
from interfaces.mobile_interface import MobileInterface


class IOSNavigationScreen:
    """
    Screen Object for iOS navigation.

    - NO decorators
    - Atomic methods (one UI action)
    - Return self for chaining
    - State-check methods for assertions

    Locators here are PLAIN TUPLES, not platform-keyed dicts, and that is
    deliberate. Every other Screen in this reference is shared across platforms,
    so its constants map a platform key to a locator and `locator()` resolves
    them at call time. This class is iOS by construction - there is no Android
    key it could ever hold - so a one-key dict would be ceremony that teaches
    the wrong lesson. Use the keyed form when a screen is shared; use plain
    tuples when a class exists precisely because the platforms differ.
    """

    def __init__(self, mobile: MobileInterface):
        """Compose MobileInterface - NO inheritance."""
        self.mobile = mobile

    # ==================== LOCATORS (Class Constants) ====================
    # Every value appears verbatim in a live XCUITest session, from run
    # 35327677124 on iPhone 16 Pro / iOS 18.6.

    CATALOG_TAB = (AppiumBy.ACCESSIBILITY_ID, "Catalog-tab-item")
    CART_TAB = (AppiumBy.ACCESSIBILITY_ID, "Cart-tab-item")
    MORE_TAB = (AppiumBy.ACCESSIBILITY_ID, "More-tab-item")

    # ==================== ATOMIC METHODS (One UI Action) ====================

    def open_catalog(self) -> "IOSNavigationScreen":
        """Go to the catalog. One tap: the tab bar is always on screen."""
        self.mobile.click(*self.CATALOG_TAB)
        return self

    def open_cart(self) -> "IOSNavigationScreen":
        """Go to the cart. One tap."""
        self.mobile.click(*self.CART_TAB)
        return self

    def open_menu(self) -> "IOSNavigationScreen":
        """Open the More tab, which is where iOS puts secondary navigation."""
        self.mobile.click(*self.MORE_TAB)
        return self

    # ==================== STATE-CHECK METHODS (For Assertions) ====================

    def is_navigation_displayed(self) -> bool:
        """Check the tab bar is showing."""
        return self.mobile.is_element_displayed(*self.CATALOG_TAB)
