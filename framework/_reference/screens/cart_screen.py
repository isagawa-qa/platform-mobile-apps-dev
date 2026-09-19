"""
CartScreen - Screen Object Model

Screen Object for the cart. Handles verifying what was added and moving on
to checkout.
"""

from appium.webdriver.common.appiumby import AppiumBy
from interfaces.mobile_interface import MobileInterface


class CartScreen:
    """
    Screen Object for the Cart.

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
    # 35441567474 on iPhone 16 Pro / iOS 18.6, captured with two units of one
    # product already in the cart.
    #
    # "ios" keys only, never "default" - no Android capture exists yet.

    SCREEN_ROOT = {"ios": (AppiumBy.ACCESSIBILITY_ID, "Cart-screen")}
    REMOVE_ITEM = {"ios": (AppiumBy.ACCESSIBILITY_ID, "Remove Item")}
    PROCEED_TO_CHECKOUT = {"ios": (AppiumBy.ACCESSIBILITY_ID, "ProceedToCheckout")}
    TOTAL_LABEL = {"ios": (AppiumBy.ACCESSIBILITY_ID, "Total:")}
    EMPTY_MESSAGE = {"ios": (AppiumBy.ACCESSIBILITY_ID, "No Items")}

    # Deliberately ABSENT, and each for a reason the capture proves:
    #
    #   line_item_count - "Remove Item" matches TWICE per row: the Button and
    #   the StaticText nested inside it carry the same name. Counting by name
    #   reports two line items for one. The app exposes no stable per-row id, so
    #   a count method here would be confidently wrong.
    #
    #   item_total / grand_total - the totals render as StaticText whose NAME is
    #   the value itself ("2 Items", "$59.98"). A locator on those is a locator
    #   on today's data: it breaks the moment the quantity or price changes.

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

    def wait_for_cart_visible(self, timeout: int = 20) -> "CartScreen":
        """Wait for the cart screen root to be visible."""
        self.mobile.wait_for_element_visible(*self.locator("SCREEN_ROOT"), timeout=timeout)
        return self

    def remove_first_item(self) -> "CartScreen":
        """Remove the first line item from the cart."""
        self.mobile.click_element_at(*self.locator("REMOVE_ITEM"), index=0)
        return self

    def open_checkout(self) -> "CartScreen":
        """Proceed from the cart to checkout."""
        self.mobile.click(*self.locator("PROCEED_TO_CHECKOUT"))
        return self

    # ==================== STATE-CHECK METHODS (For Assertions) ====================

    def is_cart_displayed(self) -> bool:
        """Check the cart screen is showing."""
        return self.mobile.is_element_displayed(*self.locator("SCREEN_ROOT"))

    def is_empty(self) -> bool:
        """Check the cart is empty.

        DISPLAYED, not present. The empty-cart message sits in the accessibility
        tree even when the cart holds items - the live capture shows "No Items"
        with visible="false" alongside a populated row. An is_element_present
        check here would report every full cart as empty.
        """
        return self.mobile.is_element_displayed(*self.locator("EMPTY_MESSAGE"))

    def is_checkout_available(self) -> bool:
        """Check the cart offers Proceed To Checkout."""
        return self.mobile.is_element_displayed(*self.locator("PROCEED_TO_CHECKOUT"))

    def has_total(self) -> bool:
        """Check the cart is showing a total."""
        return self.mobile.is_element_displayed(*self.locator("TOTAL_LABEL"))
