"""
Shopper - Role module

Represents a shopper persona who browses the catalog and puts a
product in the cart. Orchestrates complete business workflows using
Task modules.
"""

from interfaces.mobile_interface import MobileInterface
from resources.utilities import autologger
from _reference.tasks.shopping_tasks import ShoppingTasks


class Shopper:
    """
    Shopper role - orchestrates shopping workflows.

    - @autologger("Role") on workflow methods
    - @autologger("Role Constructor") on __init__
    - Composes Task modules
    - Workflow methods call MULTIPLE tasks
    - NO return values
    """

    @autologger.automation_logger("Role Constructor")
    def __init__(self, mobile_interface: MobileInterface):
        """
        Initialize and compose Task modules.

        Takes no credentials or URL: a native app is launched by the
        session's capabilities, not navigated to.

        Args:
            mobile_interface: MobileInterface instance
        """
        self.mobile = mobile_interface
        self.shopping_tasks = ShoppingTasks(mobile_interface)

    # ==================== WORKFLOW METHODS ====================

    @autologger.automation_logger("Role")
    def add_product_to_cart(self, index: int = 0, quantity: int = 1) -> None:
        """
        Complete workflow: browse the catalog and add a product to the cart.

        Orchestrates MULTIPLE task operations:
        1. Open the catalog
        2. Open a product
        3. Add it to the cart
        """
        self.shopping_tasks.open_catalog()
        self.shopping_tasks.open_product(index)
        self.shopping_tasks.add_product_to_cart(quantity)

    @autologger.automation_logger("Role")
    def review_cart(self) -> None:
        """
        Complete workflow: open the catalog, then the cart.

        Orchestrates MULTIPLE task operations:
        1. Open the catalog so the tab bar is in a known state
        2. Open the cart
        """
        self.shopping_tasks.open_catalog()
        self.shopping_tasks.open_cart()
