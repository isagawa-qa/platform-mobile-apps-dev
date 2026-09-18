"""
ProductDetailScreen - Screen Object Model

Screen Object for the product detail screen. Handles selection:
read the product, adjust quantity, add to cart.
"""

from appium.webdriver.common.appiumby import AppiumBy
from interfaces.mobile_interface import MobileInterface


class ProductDetailScreen:
    """
    Screen Object for Product Detail.

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
    # "ios" keys only, never "default" - no Android capture exists to support a
    # cross-platform claim.

    SCREEN_ROOT = {"ios": (AppiumBy.ACCESSIBILITY_ID, "ProductDetails-screen")}
    BACK_BUTTON = {"ios": (AppiumBy.ACCESSIBILITY_ID, "BackButton Icons")}
    PRODUCT_PRICE = {"ios": (AppiumBy.ACCESSIBILITY_ID, "Price")}
    DECREASE_QUANTITY = {"ios": (AppiumBy.ACCESSIBILITY_ID, "SubtractMinus Icons")}
    QUANTITY = {"ios": (AppiumBy.ACCESSIBILITY_ID, "Amount")}
    INCREASE_QUANTITY = {"ios": (AppiumBy.ACCESSIBILITY_ID, "AddPlus Icons")}
    ADD_TO_CART_BUTTON = {"ios": (AppiumBy.ACCESSIBILITY_ID, "AddToCart")}
    COLOR_BLACK = {"ios": (AppiumBy.ACCESSIBILITY_ID, "BlackColorUnSelected Icons")}
    COLOR_BLUE = {"ios": (AppiumBy.ACCESSIBILITY_ID, "BlueColorUnSelected Icons")}
    COLOR_GRAY = {"ios": (AppiumBy.ACCESSIBILITY_ID, "GrayColorUnSelected Icons")}
    COLOR_GREEN = {"ios": (AppiumBy.ACCESSIBILITY_ID, "GreenColorUnSelected Icons")}

    def locator(self, name: str):
        """Resolve a platform-keyed locator constant for the current platform."""
        entry = getattr(self, name)
        return entry.get(self.mobile.platform) or entry["ios"]

    # ==================== ATOMIC METHODS (One UI Action) ====================

    def wait_for_detail_visible(self, timeout: int = 20) -> "ProductDetailScreen":
        """Wait for the product detail screen root to be visible."""
        self.mobile.wait_for_element_visible(*self.locator("SCREEN_ROOT"), timeout=timeout)
        return self

    def increase_quantity(self) -> "ProductDetailScreen":
        """Increase the quantity by one."""
        self.mobile.click(*self.locator("INCREASE_QUANTITY"))
        return self

    def decrease_quantity(self) -> "ProductDetailScreen":
        """Decrease the quantity by one."""
        self.mobile.click(*self.locator("DECREASE_QUANTITY"))
        return self

    def add_to_cart(self) -> "ProductDetailScreen":
        """Add the current product to the cart."""
        self.mobile.click(*self.locator("ADD_TO_CART_BUTTON"))
        return self

    def go_back(self) -> "ProductDetailScreen":
        """Return to the previous screen."""
        self.mobile.click(*self.locator("BACK_BUTTON"))
        return self

    # ==================== STATE-CHECK METHODS (For Assertions) ====================

    def is_detail_displayed(self) -> bool:
        """Check the product detail screen is showing."""
        return self.mobile.is_element_displayed(*self.locator("SCREEN_ROOT"))

    def is_add_to_cart_available(self) -> bool:
        """Check the add-to-cart button is present and clickable."""
        return self.mobile.is_element_clickable(*self.locator("ADD_TO_CART_BUTTON"))

    def get_quantity(self) -> str:
        """Read the currently selected quantity."""
        return self.mobile.get_text(*self.locator("QUANTITY"))

    def get_price(self) -> str:
        """Read the displayed price."""
        return self.mobile.get_text(*self.locator("PRODUCT_PRICE"))
