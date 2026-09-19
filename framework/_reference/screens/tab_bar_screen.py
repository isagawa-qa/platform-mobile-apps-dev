"""
TabBarScreen - Screen Object Model

Screen Object for the bottom tab bar. Handles navigation between
the catalog, the cart and the menu.
"""

from appium.webdriver.common.appiumby import AppiumBy
from interfaces.mobile_interface import MobileInterface


class TabBarScreen:
    """
    Screen Object for the Tab Bar.

    - NO decorators
    - Locators as class constants, keyed by platform
    - Atomic methods (one UI action)
    - Return self for chaining
    - State-check methods for assertions
    """

    def __init__(self, mobile: MobileInterface):
        """Compose MobileInterface - NO inheritance."""
        self.mobile = mobile

    # ==================== LOCATORS (Class Constants) ====================
    # Every value appears verbatim in a live XCUITest session, from run
    # 35327677124 on iPhone 16 Pro / iOS 18.6.
    #
    # "ios" keys only, never "default" - no Android capture exists yet.

    CATALOG_TAB = {"ios": (AppiumBy.ACCESSIBILITY_ID, "Catalog-tab-item")}
    CART_TAB = {"ios": (AppiumBy.ACCESSIBILITY_ID, "Cart-tab-item")}
    MORE_TAB = {"ios": (AppiumBy.ACCESSIBILITY_ID, "More-tab-item")}

    def locator(self, name: str):
        """Resolve a platform-keyed locator constant for the current platform.

        Missing keys raise. A silent fall back to another platform's id is worse
        than failing: the id was never captured on this platform, so at best the
        run dies later with a confusing NoSuchElement, and at worst it matches
        something that happens to share the id and the test passes for the wrong
        reason. An uncaptured platform is a gap to report, not one to paper over.
        """
        entry = getattr(self, name)
        platform = self.mobile.platform
        if platform not in entry:
            raise KeyError(
                f"{type(self).__name__}.{name} has no {platform!r} locator "
                f"(present: {sorted(entry)}). Capture the screen on {platform} "
                f"and add the id - do not reuse another platform's."
            )
        return entry[platform]

    # ==================== ATOMIC METHODS (One UI Action) ====================

    def open_catalog(self) -> "TabBarScreen":
        """Switch to the catalog tab."""
        self.mobile.click(*self.locator("CATALOG_TAB"))
        return self

    def open_cart(self) -> "TabBarScreen":
        """Switch to the cart tab."""
        self.mobile.click(*self.locator("CART_TAB"))
        return self

    def open_menu(self) -> "TabBarScreen":
        """Switch to the menu tab."""
        self.mobile.click(*self.locator("MORE_TAB"))
        return self

    # ==================== STATE-CHECK METHODS (For Assertions) ====================

    def is_tab_bar_displayed(self) -> bool:
        """Check the tab bar is showing."""
        return self.mobile.is_element_displayed(*self.locator("CATALOG_TAB"))
