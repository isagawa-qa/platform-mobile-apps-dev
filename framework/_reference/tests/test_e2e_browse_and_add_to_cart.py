"""
TestE2EBrowseAndAddToCart - Integration test for the shopping flow.

End-to-end test that validates the complete workflow: browse the catalog,
open a product, add it to the cart, then verify the cart. Uses one Role
(Shopper) whose workflow methods each call MULTIPLE tasks, because the
output of phase 1 (a product is open) is the input to phase 2 (that product
is added).

Uses AAA pattern: Arrange, Act, Assert.
"""

import pytest
from resources.utilities import autologger
from _reference.roles.shopper import Shopper
from _reference.screens.product_catalog_screen import ProductCatalogScreen
from _reference.screens.product_detail_screen import ProductDetailScreen
from _reference.screens.cart_screen import CartScreen


class TestE2EBrowseAndAddToCart:
    """
    Integration test - shopping end-to-end flow.

    - @autologger("Test") decorator
    - MULTIPLE Role workflow calls (integration test)
    - Assert via Screen Object state-check methods from EVERY phase
    - Validates causal dependency: a product must be open before it can be
      added, and must be added before the cart can show it
    """

    @pytest.fixture(autouse=True)
    def setup(self, mobile, device, test_users):
        """Pytest fixture wires mobile, device, and test data into the test class."""
        self.mobile = mobile
        self.device = device
        self.test_users = test_users
        self.catalog_screen = ProductCatalogScreen(self.mobile)
        self.product_detail_screen = ProductDetailScreen(self.mobile)
        self.cart_screen = CartScreen(self.mobile)

    # ==================== TEST METHODS ====================

    @pytest.mark.ios
    @autologger.automation_logger("Test")
    def test_e2e_browse_and_add_to_cart(self):
        """
        Integration test: browse the catalog, add a product, verify the cart.

        AAA Pattern:
        1. Arrange - Create the Shopper role, choose the product position
        2. Act - Call Shopper.add_product_to_cart, then Shopper.review_cart
        3. Assert - Verify each phase left the app in the state the next needs

        Each assertion checks a DIFFERENT screen, because a workflow that
        navigates is only proven by the state it leaves behind on each screen
        it passes through. Asserting one thing at the end would pass even if
        the middle of the flow did nothing.

        There is no login_url and no navigate step: a native app is launched
        by the session's capabilities, not navigated to.
        """
        # Arrange
        shopper = Shopper(self.mobile)
        product_index = 0
        quantity = 2

        # Assert - precondition: the catalog rendered before anything was done
        assert self.catalog_screen.product_count() > 0, \
            "expected the catalog to render at least one product tile"

        # Act - phase 1: open a product and add it
        shopper.add_product_to_cart(product_index, quantity)

        # Assert - phase 1 landed on the product detail screen
        assert self.product_detail_screen.is_add_to_cart_available(), \
            "expected the product detail screen to offer Add To Cart"

        # Act - phase 2: go and look at what was added
        shopper.review_cart()

        # Assert - phase 2: the cart is showing, and it is NOT empty
        assert self.cart_screen.is_cart_displayed(), \
            "expected the cart screen to be displayed after review_cart"
        assert not self.cart_screen.is_empty(), \
            "expected the cart to hold the product that was just added"
        assert self.cart_screen.has_total(), \
            "expected the cart to show a total"
        assert self.cart_screen.is_checkout_available(), \
            "expected a populated cart to offer Proceed To Checkout"
