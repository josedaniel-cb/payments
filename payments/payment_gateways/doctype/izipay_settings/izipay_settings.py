# Copyright (c) 2017, Frappe Technologies and contributors
# License: MIT. See LICENSE

from urllib.parse import urlencode

import frappe
from frappe import _
from frappe.integrations.utils import create_request_log, make_get_request
from frappe.model.document import Document
from frappe.utils import call_hook_method, cint, flt, get_url

from payments.utils import create_payment_gateway


class IzipaySettings(Document):
    supported_currencies = [
        "PEN",
    ]

    currency_wise_minimum_charge_amount = {
        "PEN": 1,
    }

    def __init__(self, *args, **kwargs):
        self.gateway_name: str
        self.publishable_key: str
        # self.column_break_3: str
        self.secret_key: str
        # self.section_break_5: str
        # self.header_img: str
        # self.column_break_7: str
        self.redirect_url: str
        super().__init__(*args, **kwargs)

    def on_update(self):
        create_payment_gateway(
            "Izipay-" + self.gateway_name,
            settings="Izipay Settings",
            controller=self.gateway_name,
        )
        call_hook_method("payment_gateway_enabled", gateway="Izipay-" + self.gateway_name)
        if not self.flags.ignore_mandatory:
            self.validate_stripe_credentails()

    def validate_stripe_credentails(self):
        if self.publishable_key and self.secret_key:
            header = {
                "Authorization": "Bearer {}".format(
                    self.get_password(fieldname="secret_key", raise_exception=False)
                )
            }
            try:
                make_get_request(url="https://api.stripe.com/v1/charges", headers=header)
            except Exception:
                frappe.throw(_("Seems Publishable Key or Secret Key is wrong !!!"))

    def validate_transaction_currency(self, currency):
        if currency not in self.supported_currencies:
            frappe.throw(
                _(
                    "Please select another payment method. Izipay does not support transactions in currency '{0}'"
                ).format(currency)
            )

    def validate_minimum_transaction_amount(self, currency, amount):
        if currency in self.currency_wise_minimum_charge_amount:
            if flt(amount) < self.currency_wise_minimum_charge_amount.get(currency, 0.0):
                frappe.throw(
                    _("For currency {0}, the minimum transaction amount should be {1}").format(
                        currency, self.currency_wise_minimum_charge_amount.get(currency, 0.0)
                    )
                )

    def get_payment_url(self, **kwargs):
        return get_url(f"./stripe_checkout?{urlencode(kwargs)}")

    def create_request(self, data):
        import stripe

        self.data = frappe._dict(data)
        stripe.api_key = self.get_password(fieldname="secret_key", raise_exception=False)
        stripe.default_http_client = stripe.http_client.RequestsClient()

        try:
            self.integration_request = create_request_log(self.data, service_name="Izipay")
            return self.create_charge_on_stripe()

        except Exception:
            frappe.log_error(frappe.get_traceback())
            return {
                "redirect_to": frappe.redirect_to_message(
                    _("Server Error"),
                    _(
                        "It seems that there is an issue with the server's stripe configuration. In case of failure, the amount will get refunded to your account."
                    ),
                ),
                "status": 401,
            }

    def create_charge_on_stripe(self):
        import stripe

        try:
            charge = stripe.Charge.create(
                amount=cint(flt(self.data.amount) * 100),
                currency=self.data.currency,
                source=self.data.stripe_token_id,
                description=self.data.description,
                receipt_email=self.data.payer_email,
            )

            if charge.captured == True:
                self.integration_request.db_set("status", "Completed", update_modified=False)
                self.flags.status_changed_to = "Completed"

            else:
                frappe.log_error(charge.failure_message, "Izipay Payment not completed")

        except Exception:
            frappe.log_error(frappe.get_traceback())

        return self.finalize_request()

    def finalize_request(self):
        redirect_to = self.data.get("redirect_to") or None
        redirect_message = self.data.get("redirect_message") or None
        status = self.integration_request.status

        if self.flags.status_changed_to == "Completed":
            if self.data.reference_doctype and self.data.reference_docname:
                custom_redirect_to = None
                try:
                    custom_redirect_to = frappe.get_doc(
                        self.data.reference_doctype, self.data.reference_docname
                    ).run_method("on_payment_authorized", self.flags.status_changed_to)
                except Exception:
                    frappe.log_error(frappe.get_traceback())

                if custom_redirect_to:
                    redirect_to = custom_redirect_to

                redirect_url = "payment-success?doctype={}&docname={}".format(
                    self.data.reference_doctype, self.data.reference_docname
                )

            if self.redirect_url:
                redirect_url = self.redirect_url
                redirect_to = None
        else:
            redirect_url = "payment-failed"

        redirect_url: str
        if redirect_to and "?" in redirect_url:
            redirect_url += "&" + urlencode({"redirect_to": redirect_to})
        else:
            redirect_url += "?" + urlencode({"redirect_to": redirect_to})

        if redirect_message:
            redirect_url += "&" + urlencode({"redirect_message": redirect_message})

        return {"redirect_to": redirect_url, "status": status}


def get_gateway_controller(doctype, docname):
    reference_doc = frappe.get_doc(doctype, docname)
    gateway_controller = frappe.db.get_value(
        "Payment Gateway", reference_doc.payment_gateway, "gateway_controller"
    )
    return gateway_controller
