"""
ShoppingTasks - Task module

Orchestrates screen objects to accomplish shopping workflows.
Handles browsing the catalog and adding a product to the cart as
domain operations.
"""

from interfaces.mobile_interface import MobileInterface
from _reference.screens.product_catalog_screen import ProductCatalogScreen
from _reference.screens.product_detail_screen import ProductDetailScreen
from _reference.screens.tab_bar_screen import TabBarScreen
from resources.utilities import autologger


class ShoppingTasks:
    """
    Task module for the Shopping workflow.

    - @autologger("Task") on all methods
    - NO decorator on constructor
    - Composes Screen Objects
    - One domain operation per method
    - NO return values
    """

    def __init__(self, mobile: MobileInterface):
        """
        Compose Screen Objects — NO decorator on constructor.

        Args:
            mobile: MobileInterface instance
        """
        self.mobile = mobile
        self.catalog_screen = ProductCatalogScreen(mobile)
        self.product_detail_screen = ProductDetailScreen(mobile)
        self.tab_bar_screen = TabBarScreen(mobile)

    # ==================== TASK METHODS ====================

    @autologger.automation_logger("Task")
    def open_catalog(self) -> None:
        """
        Open the product catalog and wait for it to render.

        A native app has no URL, so there is no navigate step: the app is
        already launched by the session's capabilities.
        """
        (self.tab_bar_screen
            .open_catalog())
        (self.catalog_screen
            .wait_for_catalog_visible())

    @autologger.automation_logger("Task")
    def open_product(self, index: int = 0) -> None:
        """
        Open a product from the catalog by position.

        Selection is by position rather than by name: every catalog tile
        carries the same generic accessibility id, so no per-product
        locator exists.

        Args:
            index: Zero-based position of the product tile
        """
        (self.catalog_screen
            .scroll_to_product_item()
            .open_product_at(index))
        (self.product_detail_screen
            .wait_for_detail_visible())

    @autologger.automation_logger("Task")
    def add_product_to_cart(self, quantity: int = 1) -> None:
        """
        Add the open product to the cart at the requested quantity.

        Args:
            quantity: How many units to add
        """
        for _ in range(quantity - 1):
            self.product_detail_screen.increase_quantity()
        self.product_detail_screen.add_to_cart()

    @autologger.automation_logger("Task")
    def open_cart(self) -> None:
        """Open the cart tab."""
        self.tab_bar_screen.open_cart()
