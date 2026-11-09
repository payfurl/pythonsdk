"""The API's parts, as attributes of `PayfurlClient`: `client.charges.create_with_card(...)`."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING
from urllib.parse import quote

from .models import (
    BatchData,
    BatchList,
    BatchSearch,
    BatchStatus,
    ChargeData,
    ChargeList,
    ChargeSearch,
    CreatePaymentLink,
    CustomerData,
    CustomerList,
    CustomerSearch,
    Dispute,
    DisputeList,
    DisputeSearch,
    InfoProviders,
    NewChargeBankPayment,
    NewChargeCard,
    NewChargeCardLeastCost,
    NewChargeCustomer,
    NewChargeNetworkToken,
    NewChargePaymentMethod,
    NewChargeToken,
    NewCustomerBankPayment,
    NewCustomerCard,
    NewCustomerPayTo,
    NewCustomerProviderToken,
    NewCustomerToken,
    NewPaymentMethodBankPayment,
    NewPaymentMethodCard,
    NewPaymentMethodToken,
    NewPaymentMethodVault,
    NewPayToAgreement,
    NewProvider,
    NewProviderToken,
    NewTransactionPaymentMethod,
    NewTransferGroup,
    NewVault,
    NewWebhookSubscription,
    PaymentLink,
    PaymentLinkList,
    PaymentLinkSearch,
    PaymentMethodData,
    PaymentMethodList,
    PaymentMethodSearch,
    Provider,
    Settlement,
    SingleUseToken,
    Subscription,
    SubscriptionCreate,
    SubscriptionList,
    SubscriptionSearch,
    SubscriptionStatus,
    SubscriptionUpdate,
    TokenData,
    TokenList,
    TokenSearch,
    TransferData,
    TransferList,
    TransferSearch,
    UpdateCustomer,
    UpdatePaymentMethod,
    UpdateProvider,
    UpdateSubscriptionStatus,
    VaultData,
    VaultDataWithPCI,
    WebhookSubscription,
    WebhookSubscriptionList,
    WebhookSubscriptionSearch,
)

if TYPE_CHECKING:
    from ._client import PayfurlClient


def _id(value: str, name: str) -> str:
    """A resource id as a path segment. An empty one would call another endpoint (GET /charge/ is a search)."""
    if not value or not value.strip():
        raise ValueError(f"{name} is empty")
    return quote(value, safe="")


class _Resource:
    def __init__(self, client: PayfurlClient) -> None:
        self._client = client


class Batches(_Resource):
    def create_with_payment_methods(self, batch: NewTransactionPaymentMethod) -> BatchStatus:
        """`POST /batch/transaction/payment_method`: charges saved payment methods in one batch."""
        return self._client._call("POST", "/batch/transaction/payment_method", BatchStatus, body=batch)

    def get(self, batch_id: str) -> BatchData:
        """`GET /batch/{batchId}`."""
        return self._client._call("GET", f"/batch/{_id(batch_id, 'batch_id')}", BatchData)

    def status(self, batch_id: str) -> BatchStatus:
        """`GET /batch/{batchId}/status`."""
        return self._client._call("GET", f"/batch/{_id(batch_id, 'batch_id')}/status", BatchStatus)

    def search(self, search: BatchSearch | None = None) -> BatchList:
        """`GET /batch`."""
        return self._client._call("GET", "/batch", BatchList, query=search)


class Charges(_Resource):
    def create_with_card(self, charge: NewChargeCard) -> ChargeData:
        """`POST /charge/card`: charges a card with the provider in `charge.provider_id`."""
        return self._client._call("POST", "/charge/card", ChargeData, body=charge)

    def create_with_card_least_cost(self, charge: NewChargeCardLeastCost) -> ChargeData:
        """`POST /charge/card/least_cost`: charges a card with the account's cheapest provider for it."""
        return self._client._call("POST", "/charge/card/least_cost", ChargeData, body=charge)

    def create_with_customer(self, charge: NewChargeCustomer) -> ChargeData:
        """`POST /charge/customer`: charges a customer's default payment method."""
        return self._client._call("POST", "/charge/customer", ChargeData, body=charge)

    def create_with_payment_method(self, charge: NewChargePaymentMethod) -> ChargeData:
        """`POST /charge/payment_method`: charges a saved payment method."""
        return self._client._call("POST", "/charge/payment_method", ChargeData, body=charge)

    def create_with_token(self, charge: NewChargeToken) -> ChargeData:
        """`POST /charge/token`: charges a token from the browser SDK."""
        return self._client._call("POST", "/charge/token", ChargeData, body=charge)

    def create_with_bank_account(self, charge: NewChargeBankPayment) -> ChargeData:
        """`POST /charge/bank_account`: a direct debit; the charge stays `PENDING` until the bank settles it."""
        return self._client._call("POST", "/charge/bank_account", ChargeData, body=charge)

    def create_with_network_token(self, charge: NewChargeNetworkToken) -> ChargeData:
        """`POST /charge/network_token`."""
        return self._client._call("POST", "/charge/network_token", ChargeData, body=charge)

    def get(self, charge_id: str) -> ChargeData:
        """`GET /charge/{chargeId}`."""
        return self._client._call("GET", f"/charge/{_id(charge_id, 'charge_id')}", ChargeData)

    def search(self, search: ChargeSearch | None = None) -> ChargeList:
        """`GET /charge`."""
        return self._client._call("GET", "/charge", ChargeList, query=search)

    def refund(self, charge_id: str, amount: Decimal | None = None, comment: str | None = None) -> ChargeData:
        """`DELETE /charge/{chargeId}`: refunds the charge, all of it when `amount` is `None`."""
        return self._client._call(
            "DELETE",
            f"/charge/{_id(charge_id, 'charge_id')}",
            ChargeData,
            query={"amount": amount, "comment": comment},
        )

    def capture(self, charge_id: str, amount: Decimal | None = None) -> ChargeData:
        """`POST /charge/{chargeId}/capture`: captures an authorised charge (`capture=False`), all of it when
        `amount` is `None`."""
        return self._client._call(
            "POST", f"/charge/{_id(charge_id, 'charge_id')}/capture", ChargeData, body={"amount": amount}
        )

    def void(self, charge_id: str) -> ChargeData:
        """`DELETE /charge/{chargeId}/void`: cancels an authorised charge."""
        return self._client._call("DELETE", f"/charge/{_id(charge_id, 'charge_id')}/void", ChargeData)


class Customers(_Resource):
    def create_with_card(self, customer: NewCustomerCard) -> CustomerData:
        """`POST /customer/card`."""
        return self._client._call("POST", "/customer/card", CustomerData, body=customer)

    def create_with_token(self, customer: NewCustomerToken) -> CustomerData:
        """`POST /customer/token`."""
        return self._client._call("POST", "/customer/token", CustomerData, body=customer)

    def create_with_pay_to(self, customer: NewCustomerPayTo) -> CustomerData:
        """`POST /customer/payto`."""
        return self._client._call("POST", "/customer/payto", CustomerData, body=customer)

    def create_with_provider_token(self, customer: NewCustomerProviderToken) -> CustomerData:
        """`POST /customer/provider_token`: a customer from a token the provider issued."""
        return self._client._call("POST", "/customer/provider_token", CustomerData, body=customer)

    def create_with_single_use_token(self, customer: SingleUseToken) -> CustomerData:
        """`POST /customer/provider_single_use_token`."""
        return self._client._call("POST", "/customer/provider_single_use_token", CustomerData, body=customer)

    def create_with_bank_account(self, customer: NewCustomerBankPayment) -> CustomerData:
        """`POST /customer/bank_account`."""
        return self._client._call("POST", "/customer/bank_account", CustomerData, body=customer)

    def get(self, customer_id: str) -> CustomerData:
        """`GET /customer/{customerId}`."""
        return self._client._call("GET", f"/customer/{_id(customer_id, 'customer_id')}", CustomerData)

    def search(self, search: CustomerSearch | None = None) -> CustomerList:
        """`GET /customer`."""
        return self._client._call("GET", "/customer", CustomerList, query=search)

    def update(self, customer_id: str, customer: UpdateCustomer) -> CustomerData:
        """`PUT /customer/{customerId}`."""
        return self._client._call("PUT", f"/customer/{_id(customer_id, 'customer_id')}", CustomerData, body=customer)

    def delete(self, customer_id: str, gateway_delete: bool | None = None) -> CustomerData:
        """`DELETE /customer/{customerId}`: removes the customer and its payment methods. `gateway_delete=False`
        keeps them at the gateway (the API's default is to delete them there too)."""
        return self._client._call(
            "DELETE",
            f"/customer/{_id(customer_id, 'customer_id')}",
            CustomerData,
            query={"gatewayDelete": gateway_delete},
        )

    def payment_methods(self, customer_id: str) -> list[PaymentMethodData]:
        """`GET /customer/{customerId}/payment_method`."""
        return self._client._call(
            "GET", f"/customer/{_id(customer_id, 'customer_id')}/payment_method", list[PaymentMethodData]
        )

    def add_payment_method_with_card(self, customer_id: str, payment_method: NewPaymentMethodCard) -> PaymentMethodData:
        """`POST /customer/{customerId}/payment_method/card`."""
        path = f"/customer/{_id(customer_id, 'customer_id')}/payment_method/card"
        return self._client._call("POST", path, PaymentMethodData, body=payment_method)

    def add_payment_method_with_token(
        self, customer_id: str, payment_method: NewPaymentMethodToken
    ) -> PaymentMethodData:
        """`POST /customer/{customerId}/payment_method/token`."""
        path = f"/customer/{_id(customer_id, 'customer_id')}/payment_method/token"
        return self._client._call("POST", path, PaymentMethodData, body=payment_method)

    def add_payment_method_with_pay_to(self, customer_id: str, agreement: NewPayToAgreement) -> PaymentMethodData:
        """`POST /customer/{customerId}/payment_method/payto`."""
        path = f"/customer/{_id(customer_id, 'customer_id')}/payment_method/payto"
        return self._client._call("POST", path, PaymentMethodData, body=agreement)

    def add_payment_method_with_bank_account(
        self, customer_id: str, payment_method: NewPaymentMethodBankPayment
    ) -> PaymentMethodData:
        """`POST /customer/{customerId}/bank_account`."""
        path = f"/customer/{_id(customer_id, 'customer_id')}/bank_account"
        return self._client._call("POST", path, PaymentMethodData, body=payment_method)


class Disputes(_Resource):
    def get(self, dispute_id: str) -> Dispute:
        """`GET /dispute/{disputeId}`."""
        return self._client._call("GET", f"/dispute/{_id(dispute_id, 'dispute_id')}", Dispute)

    def search(self, search: DisputeSearch | None = None) -> DisputeList:
        """`GET /dispute`."""
        return self._client._call("GET", "/dispute", DisputeList, query=search)


class Info(_Resource):
    def providers(
        self,
        amount: Decimal | None = None,
        currency: str | None = None,
        *,
        browser_sdk_version: str | None = None,
        card_provider_id: str | None = None,
    ) -> InfoProviders:
        """`GET /info/providers`: the payment methods a checkout of this amount and currency can show.

        Uses the secret key, or the public key when the client has no secret key. `browser_sdk_version` is the
        version of the browser SDK (@payfurl/client) the checkout runs, such as `4.11.0`: the API lists PayPal only
        for version 4 or later. `card_provider_id` is the provider the checkout's cards go to, for its 3DS and network
        token options.
        """
        return self._client._call(
            "GET",
            "/info/providers",
            InfoProviders,
            query={"amount": amount, "currency": currency, "cardProviderId": card_provider_id},
            auth="secret" if self._client.secret_key else "public",
            headers={"sdk-version": browser_sdk_version} if browser_sdk_version else None,
        )


class PaymentLinks(_Resource):
    def create(self, payment_link: CreatePaymentLink) -> PaymentLink:
        """`POST /payment_link`."""
        return self._client._call("POST", "/payment_link", PaymentLink, body=payment_link)

    def get(self, payment_link_id: str) -> PaymentLink:
        """`GET /payment_link/{paymentLinkId}`."""
        return self._client._call("GET", f"/payment_link/{_id(payment_link_id, 'payment_link_id')}", PaymentLink)

    def search(self, search: PaymentLinkSearch | None = None) -> PaymentLinkList:
        """`GET /payment_link`."""
        return self._client._call("GET", "/payment_link", PaymentLinkList, query=search)


class PaymentMethods(_Resource):
    def create_with_card(self, payment_method: NewPaymentMethodCard) -> PaymentMethodData:
        """`POST /payment_method/card`."""
        return self._client._call("POST", "/payment_method/card", PaymentMethodData, body=payment_method)

    def create_with_vault(self, payment_method: NewPaymentMethodVault) -> PaymentMethodData:
        """`POST /payment_method/vault`: a payment method from a card in the vault."""
        return self._client._call("POST", "/payment_method/vault", PaymentMethodData, body=payment_method)

    def create_with_pay_to(self, agreement: NewPayToAgreement) -> PaymentMethodData:
        """`POST /payment_method/payto`."""
        return self._client._call("POST", "/payment_method/payto", PaymentMethodData, body=agreement)

    def create_with_token(self, payment_method: NewPaymentMethodToken) -> PaymentMethodData:
        """`POST /payment_method/token`."""
        return self._client._call("POST", "/payment_method/token", PaymentMethodData, body=payment_method)

    def create_with_single_use_token(self, payment_method: SingleUseToken) -> PaymentMethodData:
        """`POST /payment_method/provider_single_use_token`."""
        return self._client._call(
            "POST", "/payment_method/provider_single_use_token", PaymentMethodData, body=payment_method
        )

    def create_with_provider_token(self, payment_method: NewProviderToken) -> PaymentMethodData:
        """`POST /payment_method/provider_token`."""
        return self._client._call("POST", "/payment_method/provider_token", PaymentMethodData, body=payment_method)

    def create_with_bank_account(self, payment_method: NewPaymentMethodBankPayment) -> PaymentMethodData:
        """`POST /payment_method/bank_account`."""
        return self._client._call("POST", "/payment_method/bank_account", PaymentMethodData, body=payment_method)

    def get(self, payment_method_id: str) -> PaymentMethodData:
        """`GET /payment_method/{paymentMethodId}`."""
        path = f"/payment_method/{_id(payment_method_id, 'payment_method_id')}"
        return self._client._call("GET", path, PaymentMethodData)

    def search(self, search: PaymentMethodSearch | None = None) -> PaymentMethodList:
        """`GET /payment_method`."""
        return self._client._call("GET", "/payment_method", PaymentMethodList, query=search)

    def update(self, payment_method_id: str, payment_method: UpdatePaymentMethod) -> PaymentMethodData:
        """`PUT /payment_method/{paymentMethodId}`."""
        path = f"/payment_method/{_id(payment_method_id, 'payment_method_id')}"
        return self._client._call("PUT", path, PaymentMethodData, body=payment_method)

    def delete(self, payment_method_id: str, gateway_delete: bool | None = None) -> PaymentMethodData:
        """`DELETE /payment_method/{paymentMethodId}`. `gateway_delete=False` keeps it at the gateway."""
        path = f"/payment_method/{_id(payment_method_id, 'payment_method_id')}"
        return self._client._call("DELETE", path, PaymentMethodData, query={"gatewayDelete": gateway_delete})


class Providers(_Resource):
    def create(self, provider: NewProvider) -> Provider:
        """`POST /provider`: adds a gateway to the account."""
        return self._client._call("POST", "/provider", Provider, body=provider)

    def update(self, provider_id: str, provider: UpdateProvider) -> Provider:
        """`PUT /provider/{providerId}`."""
        return self._client._call("PUT", f"/provider/{_id(provider_id, 'provider_id')}", Provider, body=provider)

    def delete(self, provider_id: str) -> Provider:
        """`DELETE /provider/{providerId}`."""
        return self._client._call("DELETE", f"/provider/{_id(provider_id, 'provider_id')}", Provider)


class Settlements(_Resource):
    def search(self, start_date: date, end_date: date | None = None) -> list[Settlement]:
        """`GET /settlements`: the gateways' settlements of the account's charges, from `start_date` up to `end_date`
        (today when `None`). Only the date of a `datetime` is sent."""
        return self._client._call(
            "GET",
            "/settlements",
            list[Settlement],
            query={
                "startDate": _date(start_date),
                "endDate": _date(end_date) if end_date is not None else None,
            },
        )


def _date(value: date) -> str:
    return value.strftime("%Y-%m-%d")


class Subscriptions(_Resource):
    def create(self, subscription: SubscriptionCreate) -> Subscription:
        """`POST /subscription/payment_method`: charges a saved payment method on a schedule."""
        return self._client._call("POST", "/subscription/payment_method", Subscription, body=subscription)

    def get(self, subscription_id: str) -> Subscription:
        """`GET /subscription/{subscriptionId}`."""
        return self._client._call("GET", f"/subscription/{_id(subscription_id, 'subscription_id')}", Subscription)

    def search(self, search: SubscriptionSearch | None = None) -> SubscriptionList:
        """`GET /subscription`."""
        return self._client._call("GET", "/subscription", SubscriptionList, query=search)

    def update(self, subscription_id: str, subscription: SubscriptionUpdate) -> Subscription:
        """`PUT /subscription/{subscriptionId}`. The API replaces the subscription: a field left out is cleared."""
        path = f"/subscription/{_id(subscription_id, 'subscription_id')}"
        return self._client._call("PUT", path, Subscription, body=subscription)

    def update_status(self, subscription_id: str, status: SubscriptionStatus) -> Subscription:
        """`PUT /subscription/{subscriptionId}/status`: pauses (`SUSPENDED`) or resumes (`ACTIVE`) it."""
        path = f"/subscription/{_id(subscription_id, 'subscription_id')}/status"
        return self._client._call("PUT", path, Subscription, body=UpdateSubscriptionStatus(status=status))

    def delete(self, subscription_id: str) -> Subscription:
        """`DELETE /subscription/{subscriptionId}`."""
        return self._client._call("DELETE", f"/subscription/{_id(subscription_id, 'subscription_id')}", Subscription)


class Tokens(_Resource):
    def get(self, token_id: str) -> TokenData:
        """`GET /token/{tokenId}`."""
        return self._client._call("GET", f"/token/{_id(token_id, 'token_id')}", TokenData)

    def search(self, search: TokenSearch | None = None) -> TokenList:
        """`GET /token`."""
        return self._client._call("GET", "/token", TokenList, query=search)


class Transfers(_Resource):
    def create(self, transfers: NewTransferGroup) -> list[TransferData]:
        """`POST /transfer`: splits a charge between connected accounts; one `TransferData` per transfer."""
        return self._client._call("POST", "/transfer", list[TransferData], body=transfers)

    def get(self, transfer_id: str) -> TransferData:
        """`GET /transfer/{transferId}`."""
        return self._client._call("GET", f"/transfer/{_id(transfer_id, 'transfer_id')}", TransferData)

    def search(self, search: TransferSearch | None = None) -> TransferList:
        """`GET /transfer`."""
        return self._client._call("GET", "/transfer", TransferList, query=search)


class Vaults(_Resource):
    def create(self, vault: NewVault) -> VaultData:
        """`POST /vault`: stores a card in payFURL's vault."""
        return self._client._call("POST", "/vault", VaultData, body=vault)

    def get(self, vault_id: str) -> VaultDataWithPCI:
        """`GET /vault/{vaultId}`: the card, with its full number."""
        return self._client._call("GET", f"/vault/{_id(vault_id, 'vault_id')}", VaultDataWithPCI)

    def delete(self, vault_id: str) -> VaultData:
        """`DELETE /vault/{vaultId}`."""
        return self._client._call("DELETE", f"/vault/{_id(vault_id, 'vault_id')}", VaultData)


class WebhookSubscriptions(_Resource):
    def create(self, subscription: NewWebhookSubscription) -> WebhookSubscription:
        """`POST /webhook/subscription`."""
        return self._client._call("POST", "/webhook/subscription", WebhookSubscription, body=subscription)

    def get(self, webhook_subscription_id: str) -> WebhookSubscription:
        """`GET /webhook/subscription/{id}`."""
        path = f"/webhook/subscription/{_id(webhook_subscription_id, 'webhook_subscription_id')}"
        return self._client._call("GET", path, WebhookSubscription)

    def search(self, search: WebhookSubscriptionSearch | None = None) -> WebhookSubscriptionList:
        """`GET /webhook/subscription`."""
        return self._client._call("GET", "/webhook/subscription", WebhookSubscriptionList, query=search)

    def delete(self, webhook_subscription_id: str) -> WebhookSubscription:
        """`DELETE /webhook/subscription/{id}`."""
        path = f"/webhook/subscription/{_id(webhook_subscription_id, 'webhook_subscription_id')}"
        return self._client._call("DELETE", path, WebhookSubscription)
