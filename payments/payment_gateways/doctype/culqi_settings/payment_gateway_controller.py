from abc import ABC, abstractmethod
from typing import Any


class PaymentGatewayController(ABC):
    """Abstract base class defining the interface for payment gateway controllers.

    This interface defines the methods required by
    `erpnext/accounts/doctype/payment_request/payment_request.py`.
    """

    @abstractmethod
    def validate_transaction_currency(self, currency: str) -> None:
        """This method is used to check if the given currency is supported by the payment gateway.
        If the currency is not supported, it raises an exception.

        Args:
            currency: The currency code to validate

        Raises:
            frappe.ValidationError: If currency is not supported
        """

    @abstractmethod
    def get_payment_url(self, **kwargs) -> str:
        """This method generates and returns the URL to which the user should be redirected to
        complete the payment. It typically includes necessary parameters for the payment gateway.

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
        """This method checks if the transaction amount meets the minimum required amount for the
        specified currency. If the amount is below the minimum, it raises an exception.

        Args:
            currency: The currency code of the transaction
            amount: The transaction amount to validate

        Raises:
            frappe.ValidationError: If amount is below minimum required
        """

    def request_for_payment(self, **kwargs) -> None:
        """This method is used to initiate a payment request. It typically involves preparing the
        payment data and making an API call to the payment gateway to request the payment.

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
        """This method is called when a payment request is submitted. It processes the payment
        data, validates it, and initiates the payment process, including creating a payment request
        and handling the response from the payment gateway.

        Args:
            payment_request: Payment Request document

        Returns:
            bool: Whether the payment request submission is valid
        """
