from abc import ABC, abstractmethod
from typing import Any


class PaymentGatewayController(ABC):
    """Abstract base class defining the interface for payment gateway controllers.

    This interface defines the required methods by `erpnext/accounts/doctype/payment_request/payment_request.py`.
    """

    @abstractmethod
    def validate_transaction_currency(self, currency: str) -> None:
        """Validate if the transaction currency is supported.

        Args:
            currency: The currency code to validate

        Raises:
            frappe.ValidationError: If currency is not supported
        """

    @abstractmethod
    def get_payment_url(self, **kwargs) -> str:
        """Get the URL where the customer should be redirected for payment.

        Args:
            **kwargs: Payment details including:
                - amount: Transaction amount
                - title: Title of the transaction
                - description: Description of the transaction
                - reference_doctype: Reference DocType (usually "Payment Request")
                - reference_docname: Reference document name
                - payer_email: Email of the payer
                - payer_name: Name of the payer
                - order_id: Unique order identifier
                - currency: Transaction currency

        Returns:
            str: URL where customer should be redirected
        """

    def validate_minimum_transaction_amount(self, currency: str, amount: float) -> None:
        """Validate if the transaction amount meets minimum requirements.

        Args:
            currency: The currency code of the transaction
            amount: The transaction amount to validate

        Raises:
            frappe.ValidationError: If amount is below minimum required
        """

    def request_for_payment(self, **kwargs) -> None:
        """Request a payment via the payment gateway.

        Args:
            **kwargs: Payment details including:
                - reference_doctype: Reference DocType
                - reference_docname: Reference document name
                - payment_reference: Payment reference ID
                - request_amount: Amount to request
                - sender: Email of the sender
                - currency: Transaction currency
                - payment_gateway: Name of payment gateway
        """

    def on_payment_request_submission(self, payment_request: dict[str, Any]) -> bool:
        """Optional hook called when payment request is submitted.

        Args:
            payment_request: Payment Request document

        Returns:
            bool: Whether the payment request submission is valid
        """
