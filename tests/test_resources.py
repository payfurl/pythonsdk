"""Every endpoint method: its HTTP method, path, query and body, and the type its response is parsed into."""

import json
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import pytest
import respx

from payfurl import Environment, PayfurlClient
from payfurl import models as m

URL = "https://api-au.payfurl.com"
CARD = {"cardNumber": "4111111111111111", "expiryDate": "12/30", "ccv": "123", "cardholder": "Ann"}
BANK = {"bankCode": "062000", "accountNumber": "12345678", "accountName": "Ann"}
PAYTO = {
    "payerName": "Ann",
    "payerPayIdDetails": {"payId": "ann@example.com", "payIdType": "EMAIL"},
    "description": "Rent",
    "maximumAmount": 500,
    "providerId": "p1",
}


@dataclass
class Case:
    call: Callable[[PayfurlClient], Any]
    method: str
    path: str
    returns: type | Any
    body: dict[str, Any] | None = None
    query: dict[str, str] | None = None
    response: Any = None


def body(model: type[m._Request], data: dict[str, Any]) -> Any:
    """The request model, from the JSON the test expects the SDK to send."""
    return model.model_validate(data)


CHARGE = {"amount": 20.5, "currency": "AUD", "reference": "order-1", "metadata": {"k": "v"}}

CASES = {
    # Batches
    "batches.create_with_payment_methods": Case(
        lambda c: c.batches.create_with_payment_methods(
            body(m.NewTransactionPaymentMethod, {"count": 1, "description": "d", "batch": "pm1,10.00,AUD"})
        ),
        "POST",
        "/batch/transaction/payment_method",
        m.BatchStatus,
        body={"count": 1, "description": "d", "batch": "pm1,10.00,AUD"},
    ),
    "batches.get": Case(lambda c: c.batches.get("b1"), "GET", "/batch/b1", m.BatchData),
    "batches.status": Case(lambda c: c.batches.status("b1"), "GET", "/batch/b1/status", m.BatchStatus),
    "batches.search": Case(
        lambda c: c.batches.search(m.BatchSearch(description="d", limit=5, skip=10)),
        "GET",
        "/batch",
        m.BatchList,
        query={"description": "d", "limit": "5", "skip": "10"},
    ),
    # Charges
    "charges.create_with_card": Case(
        lambda c: c.charges.create_with_card(
            body(m.NewChargeCard, {**CHARGE, "providerId": "p1", "paymentInformation": CARD, "capture": False})
        ),
        "POST",
        "/charge/card",
        m.ChargeData,
        body={**CHARGE, "providerId": "p1", "paymentInformation": CARD, "capture": False},
    ),
    "charges.create_with_card_least_cost": Case(
        lambda c: c.charges.create_with_card_least_cost(
            body(m.NewChargeCardLeastCost, {**CHARGE, "paymentInformation": CARD})
        ),
        "POST",
        "/charge/card/least_cost",
        m.ChargeData,
        body={**CHARGE, "paymentInformation": CARD},
    ),
    "charges.create_with_customer": Case(
        lambda c: c.charges.create_with_customer(body(m.NewChargeCustomer, {**CHARGE, "customerId": "cu1"})),
        "POST",
        "/charge/customer",
        m.ChargeData,
        body={**CHARGE, "customerId": "cu1"},
    ),
    "charges.create_with_payment_method": Case(
        lambda c: c.charges.create_with_payment_method(
            body(m.NewChargePaymentMethod, {**CHARGE, "paymentMethodId": "pm1", "initiator": "MERCHANT"})
        ),
        "POST",
        "/charge/payment_method",
        m.ChargeData,
        body={**CHARGE, "paymentMethodId": "pm1", "initiator": "MERCHANT"},
    ),
    "charges.create_with_token": Case(
        lambda c: c.charges.create_with_token(
            body(m.NewChargeToken, {**CHARGE, "token": "t1", "transfer": {"account": "a1", "amount": 1.5}})
        ),
        "POST",
        "/charge/token",
        m.ChargeData,
        body={**CHARGE, "token": "t1", "transfer": {"account": "a1", "amount": 1.5}},
    ),
    "charges.create_with_bank_account": Case(
        lambda c: c.charges.create_with_bank_account(
            body(m.NewChargeBankPayment, {**CHARGE, "providerId": "p1", "bankPaymentInformation": BANK})
        ),
        "POST",
        "/charge/bank_account",
        m.ChargeData,
        body={**CHARGE, "providerId": "p1", "bankPaymentInformation": BANK},
    ),
    "charges.create_with_network_token": Case(
        lambda c: c.charges.create_with_network_token(
            body(m.NewChargeNetworkToken, {**CHARGE, "networkTokenId": "nt1", "providerId": "p1"})
        ),
        "POST",
        "/charge/network_token",
        m.ChargeData,
        body={**CHARGE, "networkTokenId": "nt1", "providerId": "p1"},
    ),
    "charges.get": Case(lambda c: c.charges.get("ch1"), "GET", "/charge/ch1", m.ChargeData),
    "charges.search": Case(
        lambda c: c.charges.search(
            m.ChargeSearch(
                reference="r",
                amount_greater_than=Decimal("1E+2"),
                status=m.TransactionStatus.SUCCESS,
                payment_type=m.PaymentType.CARD,
                added_after=datetime(2026, 11, 7, 10, 15, 30, tzinfo=UTC),
                card_number="4111",
                sort_by="DateAdded",
                limit=1,
            )
        ),
        "GET",
        "/charge",
        m.ChargeList,
        query={
            "reference": "r",
            "amountGreaterThan": "100",
            "status": "SUCCESS",
            "paymentType": "CARD",
            "addedAfter": "2026-11-07T10:15:30Z",
            "cardNumber": "4111",
            "sortBy": "DateAdded",
            "limit": "1",
        },
    ),
    "charges.search (no filters)": Case(lambda c: c.charges.search(), "GET", "/charge", m.ChargeList, query={}),
    "charges.refund": Case(
        lambda c: c.charges.refund("ch1", Decimal("5.50"), "Damaged & late #2"),
        "DELETE",
        "/charge/ch1",
        m.ChargeData,
        query={"amount": "5.50", "comment": "Damaged & late #2"},
    ),
    "charges.refund (all)": Case(lambda c: c.charges.refund("ch1"), "DELETE", "/charge/ch1", m.ChargeData, query={}),
    "charges.capture": Case(
        lambda c: c.charges.capture("ch1", Decimal("5.5")),
        "POST",
        "/charge/ch1/capture",
        m.ChargeData,
        body={"amount": 5.5},
    ),
    "charges.capture (all)": Case(
        lambda c: c.charges.capture("ch1"), "POST", "/charge/ch1/capture", m.ChargeData, body={}
    ),
    "charges.void": Case(lambda c: c.charges.void("ch1"), "DELETE", "/charge/ch1/void", m.ChargeData),
    # Customers
    "customers.create_with_card": Case(
        lambda c: c.customers.create_with_card(
            body(m.NewCustomerCard, {"providerId": "p1", "paymentInformation": CARD, "email": "a@b.c"})
        ),
        "POST",
        "/customer/card",
        m.CustomerData,
        body={"providerId": "p1", "paymentInformation": CARD, "email": "a@b.c"},
    ),
    "customers.create_with_token": Case(
        lambda c: c.customers.create_with_token(body(m.NewCustomerToken, {"token": "t1", "reference": "r"})),
        "POST",
        "/customer/token",
        m.CustomerData,
        body={"token": "t1", "reference": "r"},
    ),
    "customers.create_with_pay_to": Case(
        lambda c: c.customers.create_with_pay_to(body(m.NewCustomerPayTo, {"payToAgreement": PAYTO})),
        "POST",
        "/customer/payto",
        m.CustomerData,
        body={"payToAgreement": PAYTO},
    ),
    "customers.create_with_provider_token": Case(
        lambda c: c.customers.create_with_provider_token(
            body(m.NewCustomerProviderToken, {"providerId": "p1", "providerToken": "gw1"})
        ),
        "POST",
        "/customer/provider_token",
        m.CustomerData,
        body={"providerId": "p1", "providerToken": "gw1"},
    ),
    "customers.create_with_single_use_token": Case(
        lambda c: c.customers.create_with_single_use_token(
            body(m.SingleUseToken, {"providerId": "p1", "providerToken": "gw1"})
        ),
        "POST",
        "/customer/provider_single_use_token",
        m.CustomerData,
        body={"providerId": "p1", "providerToken": "gw1"},
    ),
    "customers.create_with_bank_account": Case(
        lambda c: c.customers.create_with_bank_account(
            body(m.NewCustomerBankPayment, {"providerId": "p1", "bankPaymentInformation": BANK})
        ),
        "POST",
        "/customer/bank_account",
        m.CustomerData,
        body={"providerId": "p1", "bankPaymentInformation": BANK},
    ),
    "customers.get": Case(lambda c: c.customers.get("cu1"), "GET", "/customer/cu1", m.CustomerData),
    "customers.search": Case(
        lambda c: c.customers.search(m.CustomerSearch(email="a@b.c", include_removed=True)),
        "GET",
        "/customer",
        m.CustomerList,
        query={"email": "a@b.c", "includeRemoved": "true"},
    ),
    "customers.update": Case(
        lambda c: c.customers.update("cu1", body(m.UpdateCustomer, {"phone": "+61400000000"})),
        "PUT",
        "/customer/cu1",
        m.CustomerData,
        body={"phone": "+61400000000"},
    ),
    "customers.delete": Case(
        lambda c: c.customers.delete("cu1", gateway_delete=False),
        "DELETE",
        "/customer/cu1",
        m.CustomerData,
        query={"gatewayDelete": "false"},
    ),
    "customers.payment_methods": Case(
        lambda c: c.customers.payment_methods("cu1"),
        "GET",
        "/customer/cu1/payment_method",
        list[m.PaymentMethodData],
        response=[{"paymentMethodId": "pm1"}],
    ),
    "customers.add_payment_method_with_card": Case(
        lambda c: c.customers.add_payment_method_with_card(
            "cu1", body(m.NewPaymentMethodCard, {"providerId": "p1", "paymentInformation": CARD, "setDefault": True})
        ),
        "POST",
        "/customer/cu1/payment_method/card",
        m.PaymentMethodData,
        body={"providerId": "p1", "paymentInformation": CARD, "setDefault": True},
    ),
    "customers.add_payment_method_with_token": Case(
        lambda c: c.customers.add_payment_method_with_token("cu1", body(m.NewPaymentMethodToken, {"token": "t1"})),
        "POST",
        "/customer/cu1/payment_method/token",
        m.PaymentMethodData,
        body={"token": "t1"},
    ),
    "customers.add_payment_method_with_pay_to": Case(
        lambda c: c.customers.add_payment_method_with_pay_to("cu1", body(m.NewPayToAgreement, PAYTO)),
        "POST",
        "/customer/cu1/payment_method/payto",
        m.PaymentMethodData,
        body=PAYTO,
    ),
    "customers.add_payment_method_with_bank_account": Case(
        lambda c: c.customers.add_payment_method_with_bank_account(
            "cu1", body(m.NewPaymentMethodBankPayment, {"providerId": "p1", "bankPaymentInformation": BANK})
        ),
        "POST",
        "/customer/cu1/bank_account",
        m.PaymentMethodData,
        body={"providerId": "p1", "bankPaymentInformation": BANK},
    ),
    # Disputes
    "disputes.get": Case(lambda c: c.disputes.get("d1"), "GET", "/dispute/d1", m.Dispute),
    "disputes.search": Case(
        lambda c: c.disputes.search(m.DisputeSearch(transaction_id="ch1", status="Open")),
        "GET",
        "/dispute",
        m.DisputeList,
        query={"transactionId": "ch1", "status": "Open"},
    ),
    # Info
    "info.providers": Case(
        lambda c: c.info.providers(Decimal("10.00"), "AUD", browser_sdk_version="4.11.0", card_provider_id="p1"),
        "GET",
        "/info/providers",
        m.InfoProviders,
        query={"amount": "10.00", "currency": "AUD", "cardProviderId": "p1"},
    ),
    # Payment links
    "payment_links.create": Case(
        lambda c: c.payment_links.create(
            body(m.CreatePaymentLink, {"title": "Shoes", "amount": 30, "currency": "AUD", "callToAction": "Pay"})
        ),
        "POST",
        "/payment_link",
        m.PaymentLink,
        body={"title": "Shoes", "amount": 30.0, "currency": "AUD", "callToAction": "Pay"},
    ),
    "payment_links.get": Case(lambda c: c.payment_links.get("pl1"), "GET", "/payment_link/pl1", m.PaymentLink),
    "payment_links.search": Case(
        lambda c: c.payment_links.search(m.PaymentLinkSearch(added_before=datetime(2026, 1, 2, tzinfo=UTC), limit=3)),
        "GET",
        "/payment_link",
        m.PaymentLinkList,
        query={"addedBefore": "2026-01-02T00:00:00Z", "limit": "3"},
    ),
    # Payment methods
    "payment_methods.create_with_card": Case(
        lambda c: c.payment_methods.create_with_card(
            body(m.NewPaymentMethodCard, {"providerId": "p1", "paymentInformation": CARD})
        ),
        "POST",
        "/payment_method/card",
        m.PaymentMethodData,
        body={"providerId": "p1", "paymentInformation": CARD},
    ),
    "payment_methods.create_with_vault": Case(
        lambda c: c.payment_methods.create_with_vault(
            body(m.NewPaymentMethodVault, {"providerId": "p1", "paymentMethodId": "pm1", "ccv": "123"})
        ),
        "POST",
        "/payment_method/vault",
        m.PaymentMethodData,
        body={"providerId": "p1", "paymentMethodId": "pm1", "ccv": "123"},
    ),
    "payment_methods.create_with_pay_to": Case(
        lambda c: c.payment_methods.create_with_pay_to(body(m.NewPayToAgreement, PAYTO)),
        "POST",
        "/payment_method/payto",
        m.PaymentMethodData,
        body=PAYTO,
    ),
    "payment_methods.create_with_token": Case(
        lambda c: c.payment_methods.create_with_token(body(m.NewPaymentMethodToken, {"token": "t1"})),
        "POST",
        "/payment_method/token",
        m.PaymentMethodData,
        body={"token": "t1"},
    ),
    "payment_methods.create_with_single_use_token": Case(
        lambda c: c.payment_methods.create_with_single_use_token(
            body(m.SingleUseToken, {"providerId": "p1", "providerToken": "gw1"})
        ),
        "POST",
        "/payment_method/provider_single_use_token",
        m.PaymentMethodData,
        body={"providerId": "p1", "providerToken": "gw1"},
    ),
    "payment_methods.create_with_provider_token": Case(
        lambda c: c.payment_methods.create_with_provider_token(
            body(m.NewProviderToken, {"providerId": "p1", "providerToken": "gw1"})
        ),
        "POST",
        "/payment_method/provider_token",
        m.PaymentMethodData,
        body={"providerId": "p1", "providerToken": "gw1"},
    ),
    "payment_methods.create_with_bank_account": Case(
        lambda c: c.payment_methods.create_with_bank_account(
            body(m.NewPaymentMethodBankPayment, {"providerId": "p1", "bankPaymentInformation": BANK})
        ),
        "POST",
        "/payment_method/bank_account",
        m.PaymentMethodData,
        body={"providerId": "p1", "bankPaymentInformation": BANK},
    ),
    "payment_methods.get": Case(
        lambda c: c.payment_methods.get("pm1"), "GET", "/payment_method/pm1", m.PaymentMethodData
    ),
    "payment_methods.search": Case(
        lambda c: c.payment_methods.search(m.PaymentMethodSearch(customer_id="cu1")),
        "GET",
        "/payment_method",
        m.PaymentMethodList,
        query={"customerId": "cu1"},
    ),
    "payment_methods.update": Case(
        lambda c: c.payment_methods.update("pm1", body(m.UpdatePaymentMethod, {"card": {"expiryDate": "01/31"}})),
        "PUT",
        "/payment_method/pm1",
        m.PaymentMethodData,
        body={"card": {"expiryDate": "01/31"}},
    ),
    "payment_methods.delete": Case(
        lambda c: c.payment_methods.delete("pm1"), "DELETE", "/payment_method/pm1", m.PaymentMethodData, query={}
    ),
    # Providers
    "providers.create": Case(
        lambda c: c.providers.create(
            body(
                m.NewProvider,
                {
                    "type": "dummy",
                    "name": "Dummy",
                    "environment": "TEST",
                    "authenticationParameters": {"FailureAmount": "13.00"},
                    "currency": "AUD",
                },
            )
        ),
        "POST",
        "/provider",
        m.Provider,
        body={
            "type": "dummy",
            "name": "Dummy",
            "environment": "TEST",
            "authenticationParameters": {"FailureAmount": "13.00"},
            "currency": "AUD",
        },
    ),
    "providers.update": Case(
        lambda c: c.providers.update("p1", body(m.UpdateProvider, {"name": "Renamed"})),
        "PUT",
        "/provider/p1",
        m.Provider,
        body={"name": "Renamed"},
    ),
    "providers.delete": Case(lambda c: c.providers.delete("p1"), "DELETE", "/provider/p1", m.Provider),
    # Settlements
    "settlements.search": Case(
        lambda c: c.settlements.search(datetime(2026, 11, 1, 23, 0), date(2026, 11, 7)),
        "GET",
        "/settlements",
        list[m.Settlement],
        query={"startDate": "2026-11-01", "endDate": "2026-11-07"},
        response=[{"settlementId": "s1", "amount": 10}],
    ),
    # Subscriptions
    "subscriptions.create": Case(
        lambda c: c.subscriptions.create(
            body(
                m.SubscriptionCreate,
                {"paymentMethodId": "pm1", "amount": 9.95, "currency": "AUD", "interval": "Month", "frequency": 1},
            )
        ),
        "POST",
        "/subscription/payment_method",
        m.Subscription,
        body={"paymentMethodId": "pm1", "amount": 9.95, "currency": "AUD", "interval": "Month", "frequency": 1},
    ),
    "subscriptions.get": Case(lambda c: c.subscriptions.get("s1"), "GET", "/subscription/s1", m.Subscription),
    "subscriptions.search": Case(
        lambda c: c.subscriptions.search(m.SubscriptionSearch(status=m.SubscriptionStatus.ACTIVE)),
        "GET",
        "/subscription",
        m.SubscriptionList,
        query={"status": "Active"},
    ),
    "subscriptions.update": Case(
        lambda c: c.subscriptions.update(
            "s1", body(m.SubscriptionUpdate, {"amount": 5, "currency": "AUD", "interval": "Week", "frequency": 2})
        ),
        "PUT",
        "/subscription/s1",
        m.Subscription,
        body={"amount": 5.0, "currency": "AUD", "interval": "Week", "frequency": 2},
    ),
    "subscriptions.update_status": Case(
        lambda c: c.subscriptions.update_status("s1", m.SubscriptionStatus.SUSPENDED),
        "PUT",
        "/subscription/s1/status",
        m.Subscription,
        body={"status": "Suspended"},
    ),
    "subscriptions.delete": Case(lambda c: c.subscriptions.delete("s1"), "DELETE", "/subscription/s1", m.Subscription),
    # Tokens
    "tokens.get": Case(lambda c: c.tokens.get("t1"), "GET", "/token/t1", m.TokenData),
    "tokens.search": Case(
        lambda c: c.tokens.search(m.TokenSearch(provider_id="p1")),
        "GET",
        "/token",
        m.TokenList,
        query={"providerId": "p1"},
    ),
    # Transfers
    "transfers.create": Case(
        lambda c: c.transfers.create(
            body(
                m.NewTransferGroup,
                {
                    "providerId": "p1",
                    "groupReference": "g1",
                    "chargeId": "ch1",
                    "transfers": [{"account": "a1", "amount": 1.25}],
                },
            )
        ),
        "POST",
        "/transfer",
        list[m.TransferData],
        body={
            "providerId": "p1",
            "groupReference": "g1",
            "chargeId": "ch1",
            "transfers": [{"account": "a1", "amount": 1.25}],
        },
        response=[{"transferId": "tr1"}],
    ),
    "transfers.get": Case(lambda c: c.transfers.get("tr1"), "GET", "/transfer/tr1", m.TransferData),
    "transfers.search": Case(
        lambda c: c.transfers.search(m.TransferSearch(reference="g1", status="SUCCESS")),
        "GET",
        "/transfer",
        m.TransferList,
        query={"reference": "g1", "status": "SUCCESS"},
    ),
    # Vaults
    "vaults.create": Case(
        lambda c: c.vaults.create(body(m.NewVault, {"cardNumber": "4111111111111111", "expireSeconds": 60})),
        "POST",
        "/vault",
        m.VaultData,
        body={"cardNumber": "4111111111111111", "expireSeconds": 60},
    ),
    "vaults.get": Case(lambda c: c.vaults.get("v1"), "GET", "/vault/v1", m.VaultDataWithPCI),
    "vaults.delete": Case(lambda c: c.vaults.delete("v1"), "DELETE", "/vault/v1", m.VaultData),
    # Webhook subscriptions
    "webhook_subscriptions.create": Case(
        lambda c: c.webhook_subscriptions.create(
            body(m.NewWebhookSubscription, {"url": "https://shop/hook", "types": ["Transaction", "Dispute"]})
        ),
        "POST",
        "/webhook/subscription",
        m.WebhookSubscription,
        body={"url": "https://shop/hook", "types": ["Transaction", "Dispute"]},
    ),
    "webhook_subscriptions.get": Case(
        lambda c: c.webhook_subscriptions.get("w1"), "GET", "/webhook/subscription/w1", m.WebhookSubscription
    ),
    "webhook_subscriptions.search": Case(
        lambda c: c.webhook_subscriptions.search(m.WebhookSubscriptionSearch(type=m.WebhookType.TRANSACTION)),
        "GET",
        "/webhook/subscription",
        m.WebhookSubscriptionList,
        query={"type": "Transaction"},
    ),
    "webhook_subscriptions.delete": Case(
        lambda c: c.webhook_subscriptions.delete("w1"), "DELETE", "/webhook/subscription/w1", m.WebhookSubscription
    ),
}


@pytest.fixture
def api() -> Iterator[respx.MockRouter]:
    with respx.mock(base_url=URL) as router:
        yield router


@pytest.mark.parametrize("case", CASES.values(), ids=CASES.keys())
def test_endpoint(api: respx.MockRouter, case: Case) -> None:
    route = api.request(case.method, case.path).respond(json=case.response if case.response is not None else {})
    result = case.call(PayfurlClient("seclive0123-au", Environment.PRODUCTION))

    request = route.calls.last.request
    assert request.headers["x-secretkey"] == "seclive0123-au"
    if case.query is not None:
        assert dict(request.url.params) == case.query
    if case.body is None:
        assert request.content == b""
    else:
        assert json.loads(request.content) == case.body
    if isinstance(case.returns, type):
        assert isinstance(result, case.returns)
    else:
        item = case.returns.__args__[0]
        assert isinstance(result, list) and len(result) == 1 and isinstance(result[0], item)


def test_every_public_method_is_covered() -> None:
    client = PayfurlClient("seclive0123-au", Environment.PRODUCTION)
    methods = {
        f"{name}.{method}"
        for name, resource in vars(client).items()
        if not name.startswith("_") and hasattr(resource, "_client")
        for method in dir(resource)
        if not method.startswith("_")
    }
    covered = {key.split(" ")[0] for key in CASES}
    assert methods == covered


def test_info_providers_sends_the_browser_sdk_version_and_takes_the_public_key(api: respx.MockRouter) -> None:
    route = api.get("/info/providers").respond(json={"hasCardProviders": True})
    client = PayfurlClient(None, "production", public_key="publive0123-au")
    assert client.info.providers(browser_sdk_version="4.11.0").has_card_providers is True
    headers = route.calls.last.request.headers
    assert headers["x-publickey"] == "publive0123-au"
    assert headers["sdk-version"] == "4.11.0"
    assert "x-secretkey" not in headers

    PayfurlClient("seclive0123-au", "production", public_key="publive0123-au").info.providers()
    headers = route.calls.last.request.headers
    assert headers["x-secretkey"] == "seclive0123-au"
    assert "x-publickey" not in headers
    assert "sdk-version" not in headers
