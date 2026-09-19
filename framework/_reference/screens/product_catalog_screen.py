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
    # Every value below appears verbatim in a capture COMMITTED to this repo:
    #   iOS     -> _captures/ios-catalog.xml        (pending - see README)
    #   Android -> _captures/android-catalog.xml    (emulator-5554, API 34)
    # No id is typed from memory. Read the capture, then write the constant.
    #
    # This screen is the worked example of what a platform-keyed locator is FOR.
    # The same screen in the same product yields FOUR different cross-platform
    # outcomes, and each one is handled differently:
    #
    #   1. SAME id on both       -> one "default" key (SCREEN_TITLE)
    #   2. DIFFERENT id, same thing -> two keys (SCREEN_ROOT, PRODUCT_NAME, ...)
    #   3. NO counterpart         -> the key that exists, and only that one
    #                                (HEADER_TITLE: Android merges it into the logo)
    #   4. TWO constants, ONE node -> both keys point at it, with a note saying why
    #                                (PRODUCT_ITEM / PRODUCT_IMAGE on Android)
    #
    # A missing key raises rather than falling back - see locator() below.

    # 2. Different id, same element.
    SCREEN_ROOT = {
        "ios": (AppiumBy.ACCESSIBILITY_ID, "Catalog-screen"),
        "android": (AppiumBy.ACCESSIBILITY_ID, "Displays all products of catalog"),
    }

    # 3. No counterpart. iOS exposes the logo and the wordmark as two nodes;
    # Android exposes ONE ImageView (resource-id mTvTitle) described as
    # "App logo and name". HEADER_TITLE therefore stays iOS-only - inventing an
    # Android key here would be the exact "id nobody looked at" the rule forbids.
    HEADER_LOGO = {
        "ios": (AppiumBy.ACCESSIBILITY_ID, "AppLogo Icons"),
        "android": (AppiumBy.ACCESSIBILITY_ID, "App logo and name"),
    }
    HEADER_TITLE = {"ios": (AppiumBy.ACCESSIBILITY_ID, "AppTitle Icons")}

    # 1. Same id on both platforms, so the key collapses to "default". This is
    # the ONLY promotion in this file, and it is promoted because two captures
    # agree - not because the string looked generic enough to be shared.
    SCREEN_TITLE = {"default": (AppiumBy.ACCESSIBILITY_ID, "title")}

    # 4. Two constants, one node. On iOS the tile is a container ("ProductItem")
    # holding a separate image. On Android the tile ViewGroup has no id, is not
    # clickable, and the IMAGE is the tap target - so both constants resolve to
    # the same node there. PRODUCT_ITEM stays the one used for tapping and
    # counting on both platforms; the duplicate value is correct, not a typo.
    PRODUCT_ITEM = {
        "ios": (AppiumBy.ACCESSIBILITY_ID, "ProductItem"),
        "android": (AppiumBy.ACCESSIBILITY_ID, "Product Image"),
    }
    PRODUCT_IMAGE = {
        "ios": (AppiumBy.ACCESSIBILITY_ID, "Product Image"),
        "android": (AppiumBy.ACCESSIBILITY_ID, "Product Image"),
    }

    # 2. Different id, same element. Note Android says "Title" where iOS says
    # "Name" - a reminder that these strings are the app authors' choices, not a
    # convention, which is why they are read rather than guessed.
    PRODUCT_NAME = {
        "ios": (AppiumBy.ACCESSIBILITY_ID, "Product Name"),
        "android": (AppiumBy.ACCESSIBILITY_ID, "Product Title"),
    }
    PRODUCT_PRICE = {
        "ios": (AppiumBy.ACCESSIBILITY_ID, "Product Price"),
        "android": (AppiumBy.ACCESSIBILITY_ID, "Product Price"),
    }

    # PRODUCT_PRICE is NOT promoted to "default" even though both captures show
    # the same string, because the two were taken from different builds of the
    # app rather than from one cross-platform run. Two keys carrying the same
    # value assert exactly what was observed; "default" would assert more.

    # PRODUCT_BY_NAME is deliberately absent. Both captures show every tile
    # carrying the SAME generic identifier - "Product Name" on iOS, "Product
    # Title" on Android, four times each - so the catalog has no per-product
    # accessibility id and a product cannot be selected by id on either platform.
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
