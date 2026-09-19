"""
ProductCatalogScreen - Screen Object Model

Screen Object for the product catalog. Handles browsing:
wait for the catalog, read a product, open a product.
"""

from appium.webdriver.common.appiumby import AppiumBy
from interfaces.mobile_interface import MobileInterface


class ProductCatalogScreen:
    """
    Screen Object for the Product Catalog.

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
    # Every value below appears verbatim in a live XCUITest session, taken from
    # run 35327677124 on iPhone 16 Pro / iOS 18.6. No id is typed from memory.
    #
    # Keys are "ios" only, never "default". A "default" key CLAIMS the id is
    # shared with Android, and no Android capture exists to support that. Ids get
    # promoted to "default" when an Android capture shows the same string.

    SCREEN_ROOT = {"ios": (AppiumBy.ACCESSIBILITY_ID, "Catalog-screen")}
    HEADER_LOGO = {"ios": (AppiumBy.ACCESSIBILITY_ID, "AppLogo Icons")}
    HEADER_TITLE = {"ios": (AppiumBy.ACCESSIBILITY_ID, "AppTitle Icons")}
    SCREEN_TITLE = {"ios": (AppiumBy.ACCESSIBILITY_ID, "title")}
    PRODUCT_ITEM = {"ios": (AppiumBy.ACCESSIBILITY_ID, "ProductItem")}
    PRODUCT_IMAGE = {"ios": (AppiumBy.ACCESSIBILITY_ID, "Product Image")}
    PRODUCT_NAME = {"ios": (AppiumBy.ACCESSIBILITY_ID, "Product Name")}
    PRODUCT_PRICE = {"ios": (AppiumBy.ACCESSIBILITY_ID, "Product Price")}

    # PRODUCT_BY_NAME is deliberately absent. The capture shows every tile
    # carrying the SAME generic identifier "Product Name" - the catalog has no
    # per-product accessibility id, so a product cannot be selected by id at all.
    # Selection is by index (open_product_at) or by visible label, and the design
    # sheet's predicate-expression placeholder is unshippable as written.

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

    def wait_for_catalog_visible(self, timeout: int = 20) -> "ProductCatalogScreen":
        """Wait for the catalog screen root to be visible."""
        self.mobile.wait_for_element_visible(*self.locator("SCREEN_ROOT"), timeout=timeout)
        return self

    def open_product_at(self, index: int = 0) -> "ProductCatalogScreen":
        """Open the product tile at the given position."""
        self.mobile.click_element_at(*self.locator("PRODUCT_ITEM"), index=index)
        return self

    def scroll_to_product_item(self) -> "ProductCatalogScreen":
        """Scroll until a product tile is on screen."""
        self.mobile.scroll_to_element(*self.locator("PRODUCT_ITEM"))
        return self

    # ==================== STATE-CHECK METHODS (For Assertions) ====================

    def is_catalog_displayed(self) -> bool:
        """Check the catalog screen is showing."""
        return self.mobile.is_element_displayed(*self.locator("SCREEN_ROOT"))

    def product_count(self) -> int:
        """How many product tiles are currently rendered."""
        return len(self.mobile.find_elements(*self.locator("PRODUCT_ITEM")))

    def get_product_name_at(self, index: int = 0) -> str:
        """Read the visible name of the product tile at the given position."""
        return self.mobile.get_text_at(*self.locator("PRODUCT_NAME"), index=index)

    def get_product_price_at(self, index: int = 0) -> str:
        """Read the visible price of the product tile at the given position."""
        return self.mobile.get_text_at(*self.locator("PRODUCT_PRICE"), index=index)
