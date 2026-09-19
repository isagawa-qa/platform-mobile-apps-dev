"""
AndroidNavigationScreen - Screen Object Model (Android only)

Screen Object for the Android header and its drawer. Handles moving
between the catalog, the cart and the menu.

The SCREEN layer of Test -> Role -> Task -> Screen -> Interface, modelling
persistent chrome rather than a whole screen. See ios_navigation_screen.py
for the note on what the `Screen` suffix does and does not claim.
"""

from appium.webdriver.common.appiumby import AppiumBy
from interfaces.mobile_interface import MobileInterface


class AndroidNavigationScreen:
    """
    Screen Object for Android navigation.

    - NO decorators
    - Atomic methods (one UI action)
    - Return self for chaining
    - State-check methods for assertions

    This class exists because Android does not navigate the way iOS does, and
    the difference is not a matter of different ids. iOS has a persistent bottom
    tab bar, so reaching the catalog is one tap. Android has a header with a
    hamburger and a cart icon; the catalog lives inside a drawer, so reaching it
    is TWO taps - open the drawer, then pick the item.

    A platform-keyed locator cannot express that. `locator()` swaps the id a
    method uses; it cannot make a method perform an extra tap. So the divergence
    is absorbed HERE, in a per-platform class that exposes the same method names
    as its iOS counterpart. Tasks call `open_catalog()` and stay platform-blind;
    no Task, Role or Test in this reference branches on `mobile.platform`.

    Locators are plain tuples rather than platform-keyed dicts - see the note in
    ios_navigation_screen.py for why.
    """

    def __init__(self, mobile: MobileInterface):
        """Compose MobileInterface - NO inheritance."""
        self.mobile = mobile

    # ==================== LOCATORS (Class Constants) ====================
    # Every value appears verbatim in _captures/android-menu.xml (drawer open
    # over the cart) or _captures/android-cart.xml (header only).

    MENU_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "View menu")
    CART_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "View cart")
    DRAWER = (AppiumBy.ID, "com.saucelabs.mydemoapp.android:id/drawerMenu")
    MENU_LIST = (AppiumBy.ACCESSIBILITY_ID, "Recycler view for menu")

    # The drawer's items are the one place in this reference where an
    # accessibility id is not available. Every row is `itemTV`, so the
    # resource-id identifies the row TYPE, not the row - "Catalog" and "Log In"
    # share it. Only the visible text separates them, so the catalog item is
    # addressed by text via a UiSelector.
    #
    # This is a FALLBACK, not a pattern to copy. Text is the user-visible label:
    # it changes when the app is translated or reworded, and this locator breaks
    # when it does. It is used here because the app offers nothing better, and
    # it is recorded as a known fragility rather than presented as a choice.
    # Both this and an XPath on resource-id + text were verified against the
    # live drawer and each matched exactly one element; the UiSelector is
    # preferred because XPath on Android is markedly slower.
    CATALOG_ITEM = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Catalog")')

    # Log In DOES carry a content-desc, so it needs no such workaround. The two
    # rows sitting side by side - one addressable, one not - is the app's
    # inconsistency, not the platform's.
    LOGIN_ITEM = (AppiumBy.ACCESSIBILITY_ID, "Login Menu Item")

    # ==================== ATOMIC METHODS (One UI Action) ====================

    def open_catalog(self) -> "AndroidNavigationScreen":
        """Go to the catalog. TWO taps: open the drawer, then pick the item.

        The same call is one tap on iOS. That asymmetry is the entire reason
        this class exists - see the class docstring.
        """
        self.mobile.click(*self.MENU_BUTTON)
        self.mobile.wait_for_element_visible(*self.MENU_LIST)
        self.mobile.click(*self.CATALOG_ITEM)
        return self

    def open_cart(self) -> "AndroidNavigationScreen":
        """Go to the cart. One tap on the header icon - same as iOS."""
        self.mobile.click(*self.CART_BUTTON)
        return self

    def open_menu(self) -> "AndroidNavigationScreen":
        """Open the drawer, which is where Android puts secondary navigation."""
        self.mobile.click(*self.MENU_BUTTON)
        self.mobile.wait_for_element_visible(*self.MENU_LIST)
        return self

    # ==================== STATE-CHECK METHODS (For Assertions) ====================

    def is_navigation_displayed(self) -> bool:
        """Check the header is showing."""
        return self.mobile.is_element_displayed(*self.CART_BUTTON)

    def is_menu_open(self) -> bool:
        """Check the drawer is open.

        WARNING, and the sharpest example of it in this reference: when this
        drawer is open, every element of the screen BEHIND it is still reported
        `displayed="true"` in the page source. The capture proves it - with the
        drawer open over the cart, `removeBt`, `cartBt` and the whole product
        row are all still displayed, though a user cannot touch any of them.

        So on this screen `is_element_displayed` does not mean "reachable". Any
        check that needs to know whether the drawer is covering the content must
        ask about the DRAWER, as this method does, and must not infer it from
        the absence of what the drawer covers.
        """
        return self.mobile.is_element_displayed(*self.DRAWER)
