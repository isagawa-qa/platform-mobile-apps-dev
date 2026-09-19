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
    # Every value appears verbatim in a capture COMMITTED to this repo:
    #   iOS     -> _captures/ios-product-detail.xml      (pending - see README)
    #   Android -> _captures/android-product-detail.xml  (emulator-5554, API 34)
    #
    # This screen shows the OTHER half of the platform-keyed design: the two
    # platforms need different LOCATOR STRATEGIES, not just different strings.
    # Android's product name carries no content-desc, so it is addressed by
    # resource-id (AppiumBy.ID) while everything else uses ACCESSIBILITY_ID.
    # That is why each key holds its own (by, value) pair rather than the screen
    # declaring one strategy for all of its locators.
    #
    # The Android capture proves MORE than browse-and-open: the quantity
    # stepper (minusIV / plusIV), the quantity value (noTV), the price (priceTV)
    # and all four colour swatches are all in it. An earlier revision of this
    # comment claimed otherwise, because the capture was searched only for the
    # three ids that were about to be written instead of being read for
    # everything it supported. Read the capture for what it HAS, not for what
    # you already planned to write.
    #
    # Note two ids below use AppiumBy.ID rather than ACCESSIBILITY_ID: `noTV`
    # and `priceTV` carry no content-desc at all, so there is no accessibility
    # id to address them by. This is why the strategy travels inside each
    # locator tuple instead of being declared once for the screen.
    #
    # SCREEN_ROOT is where "what identifies this screen" gets decided, and on
    # Android that took measuring rather than picking. iOS has a real container,
    # `ProductDetails-screen`. Android has none: `fragment_container` is on
    # every screen in the app, so it identifies nothing.
    #
    # The obvious substitute is the hero image, `productIV` - and it is WRONG.
    # Counted across all five committed captures:
    #
    #     content-desc                                    cart  menu  detail
    #     "Displays selected product"   (productIV)          1     1      1   <- NOT unique
    #     "Displays available colors..."(colorRV)            0     0      1
    #     "Tap to add product to cart"  (cartBt)             0     0      1
    #
    # productIV is the line-item thumbnail on the cart and is still in the tree
    # under the open drawer, so an is_detail_displayed() built on it returns
    # True on two screens that are not the detail screen. It would pass every
    # happy-path run and lie the moment a test checked from the wrong place.
    #
    # `cartBt` is used instead: unique across every capture, and semantically
    # the thing that MAKES this a product detail screen - you can add this
    # product to the cart from here and nowhere else. `colorRV` is also unique
    # but was rejected as product-specific: a product with no colour options
    # would not render it.
    #
    # The rule this encodes: an anchor must be verified unique ACROSS captures,
    # not merely present in the one you are looking at. Presence in the right
    # screen is half the check; absence from every other screen is the half
    # that is easy to skip.

    SCREEN_ROOT = {
        "ios": (AppiumBy.ACCESSIBILITY_ID, "ProductDetails-screen"),
        "android": (AppiumBy.ACCESSIBILITY_ID, "Tap to add product to cart"),
    }
    BACK_BUTTON = {"ios": (AppiumBy.ACCESSIBILITY_ID, "BackButton Icons")}
    PRODUCT_PRICE = {
        "ios": (AppiumBy.ACCESSIBILITY_ID, "Price"),
        "android": (AppiumBy.ID, "com.saucelabs.mydemoapp.android:id/priceTV"),
    }
    DECREASE_QUANTITY = {
        "ios": (AppiumBy.ACCESSIBILITY_ID, "SubtractMinus Icons"),
        "android": (AppiumBy.ACCESSIBILITY_ID, "Decrease item quantity"),
    }
    QUANTITY = {
        "ios": (AppiumBy.ACCESSIBILITY_ID, "Amount"),
        "android": (AppiumBy.ID, "com.saucelabs.mydemoapp.android:id/noTV"),
    }
    INCREASE_QUANTITY = {
        "ios": (AppiumBy.ACCESSIBILITY_ID, "AddPlus Icons"),
        "android": (AppiumBy.ACCESSIBILITY_ID, "Increase item quantity"),
    }
    ADD_TO_CART_BUTTON = {
        "ios": (AppiumBy.ACCESSIBILITY_ID, "AddToCart"),
        "android": (AppiumBy.ACCESSIBILITY_ID, "Tap to add product to cart"),
    }

    # Android-only for now. iOS has no captured equivalent, so this carries one
    # key and locator() will raise if the iOS flow reaches it - a gap that
    # announces itself beats one that silently resolves to another platform's id.
    #
    # Do NOT use this to decide which screen is showing. The same content-desc
    # is the line-item thumbnail on the cart and survives under the open drawer
    # - see the SCREEN_ROOT note above. It is fine for asserting that an image
    # is rendered once you already know where you are.
    PRODUCT_IMAGE = {"android": (AppiumBy.ACCESSIBILITY_ID, "Displays selected product")}

    # WARNING - resource-id `productTV` is REUSED across screens in this app. On
    # the CATALOG it is the "Products" heading (see product_catalog_screen's
    # SCREEN_TITLE); here it is the product's name. An AppiumBy.ID lookup for
    # productTV therefore matches on both screens and returns different meanings,
    # so this locator is only safe once the detail screen is confirmed showing.
    # That is exactly why is_detail_displayed() gates the read, and why the id
    # was recorded WITH the screen it was captured on rather than on its own.
    PRODUCT_NAME = {"android": (AppiumBy.ID, "com.saucelabs.mydemoapp.android:id/productTV")}
    COLOR_BLACK = {
        "ios": (AppiumBy.ACCESSIBILITY_ID, "BlackColorUnSelected Icons"),
        "android": (AppiumBy.ACCESSIBILITY_ID, "Black color"),
    }
    COLOR_BLUE = {
        "ios": (AppiumBy.ACCESSIBILITY_ID, "BlueColorUnSelected Icons"),
        "android": (AppiumBy.ACCESSIBILITY_ID, "Blue color"),
    }
    COLOR_GRAY = {
        "ios": (AppiumBy.ACCESSIBILITY_ID, "GrayColorUnSelected Icons"),
        "android": (AppiumBy.ACCESSIBILITY_ID, "Gray color"),
    }
    COLOR_GREEN = {
        "ios": (AppiumBy.ACCESSIBILITY_ID, "GreenColorUnSelected Icons"),
        "android": (AppiumBy.ACCESSIBILITY_ID, "Green color"),
    }

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

    def get_product_name(self) -> str:
        """Read the name of the product this screen is showing.

        Exists so a test can prove the RIGHT product opened, not merely that a
        detail screen appeared. Read the tile's name before tapping it, then
        compare: an assertion that only checks "a detail screen is showing"
        passes when the wrong tile was tapped, or when the tap landed on
        something else that happens to render a detail screen.

        Only call this once is_detail_displayed() is true. On Android the
        underlying resource-id is shared with the catalog's heading, so on the
        wrong screen this returns "Products" instead of failing - see the
        WARNING on PRODUCT_NAME above.
        """
        return self.mobile.get_text(*self.locator("PRODUCT_NAME"))
