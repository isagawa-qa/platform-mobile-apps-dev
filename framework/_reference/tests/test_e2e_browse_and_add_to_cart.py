"""
TestE2EBrowseAndAddToCart - Integration test for the shopping flow.

End-to-end test that validates the complete workflow: browse the catalog,
open a product, then add it to the cart. Uses one Role (Shopper) whose
workflow methods each call MULTIPLE tasks, because the output of phase 1
(a product is open) is the input to phase 2 (that product is added).

Uses AAA pattern: Arrange, Act, Assert.
"""

import pytest
from resources.utilities import autologger
from _reference.roles.shopper import Shopper
from _reference.screens.product_catalog_screen import ProductCatalogScreen
from _reference.screens.product_detail_screen import ProductDetailScreen


class TestE2EBrowseAndAddToCart:
    """
    Integration test - shopping end-to-end flow.

    - @autologger("Test") decorator
    - MULTIPLE Role workflow calls (integration test)
    - Assert via Screen Object state-check methods from BOTH phases
    - Validates causal dependency: a product must be open before it can be added
    """

    @pytest.fixture(autouse=True)
    def setup(self, mobile, device, test_users):
        """Pytest fixture wires mobile, device, and test data into the test class."""
        self.mobile = mobile
        self.device = device
        self.test_users = test_users
        self.catalog_screen = ProductCatalogScreen(self.mobile)
        self.product_detail_screen = ProductDetailScreen(self.mobile)

    # ==================== TEST METHODS ====================

    @pytest.mark.ios
    @autologger.automation_logger("Test")
    def test_e2e_browse_and_add_to_cart(self):
        """
        Integration test: browse the catalog then add a product to the cart.

        AAA Pattern:
        1. Arrange - Create the Shopper role, choose the product position
        2. Act - Call Shopper.add_product_to_cart, then Shopper.review_cart
        3. Assert - Verify the catalog rendered AND the product was addable

        There is no login_url and no navigate step: a native app is launched
        by the session's capabilities, not navigated to.
        """
        # Arrange
        shopper = Shopper(self.mobile)
        product_index = 0
        quantity = 2

        # Act
        shopper.add_product_to_cart(product_index, quantity)

        # Assert - phase 1: the catalog rendered products
        assert self.catalog_screen.product_count() > 0, \
            "expected the catalog to render at least one product tile"

        # Assert - phase 2: the product detail screen offered add-to-cart
        assert self.product_detail_screen.is_add_to_cart_available(), \
            "expected the product detail screen to offer Add To Cart"

        # Act - review what was added
        shopper.review_cart()
