# payFURL Python SDK

The [payFURL](https://payfurl.com) payments API for Python servers: charges, customers, saved payment methods,
subscriptions, refunds and the rest of the public API, with an account's secret key. Typed: every request and
response is a [Pydantic](https://docs.pydantic.dev) model, and the package ships `py.typed`.

The API reference is at [docs.payfurl.com](https://docs.payfurl.com). Card details are collected in the browser with
payFURL's browser SDK ([`@payfurl/client`](https://www.npmjs.com/package/@payfurl/client)), which turns them into a
token; this SDK charges the token on your server.

## Install

```bash
pip install payfurl
```

Python 3.11 or later. It depends on `httpx` and `pydantic` 2.

## Quick start

```python
from decimal import Decimal

from payfurl import Environment, PayfurlClient
from payfurl.models import NewChargeToken

client = PayfurlClient("sectest...-au", Environment.SANDBOX)

charge = client.charges.create_with_token(
    NewChargeToken(amount=Decimal("20.00"), currency="AUD", token=token, reference="order-1001")
)
print(charge.charge_id, charge.status)
```

Make one client per account and reuse it: it keeps connections open. `client.close()`, or
`with PayfurlClient(...) as client:`, closes them.

## Environments and regions

| `Environment` | API |
| --- | --- |
| `SANDBOX` | `https://sandbox-api.payfurl.com`, or the key region's host, such as `https://sandbox-api-au.payfurl.com` |
| `PRODUCTION` | `https://api.payfurl.com`, or the key region's host, such as `https://api-au.payfurl.com` |
| `DEVELOPMENT` | payFURL's development environment |
| `LOCAL` | `https://localhost:5001`, a payFURL API on this machine |

A key ends in its account's region (`sectest...-au`), and the client calls that region's host. `base_url=` calls
another host. TLS certificates are verified, except with `Environment.LOCAL`, whose API serves a development
certificate.

Other options: `timeout` (seconds, per request, default 60), `max_retries` and `retry_delay` (below), `public_key`
(below) and `http_client`, an `httpx.Client` of your own for proxies or event hooks. The SDK uses a client you pass
as it is, TLS settings included, and doesn't close it.

## Models

Requests take keyword arguments in snake_case and are sent in the API's camelCase. A field you leave as `None` isn't
sent, so the API applies its default; an argument the model doesn't have is an error. Amounts are `Decimal`.

Responses have every field optional. A field this version of the SDK doesn't know is kept in `model_extra`, and an
enum value it doesn't know (a new charge status, say) is the plain string. `model_dump(by_alias=True)` gives the
API's JSON back.

## Examples

```python
from datetime import date, datetime, timezone
from decimal import Decimal

from payfurl.models import (
    CardRequestInformation,
    ChargeSearch,
    CustomerSearch,
    NewChargeCard,
    NewChargeCustomer,
    NewChargePaymentMethod,
    NewChargeToken,
    NewCustomerToken,
    NewPaymentMethodToken,
    NewTransfer,
    NewTransferGroup,
    NewVault,
    NewWebhookSubscription,
    SubscriptionCreate,
    SubscriptionInterval,
    SubscriptionStatus,
    UpdateCustomer,
    WebhookType,
)
```

### Charges

```python
# A token from the browser SDK
charge = client.charges.create_with_token(NewChargeToken(amount=Decimal("20.00"), currency="AUD", token=token))

# A card, with one of the account's providers (this puts your server in PCI DSS scope: prefer tokens)
charge = client.charges.create_with_card(
    NewChargeCard(
        amount=Decimal("20.00"),
        currency="AUD",
        provider_id=provider_id,
        payment_information=CardRequestInformation(card_number="4111111111111111", expiry_date="12/30", ccv="123"),
    )
)

# A saved payment method, or a customer's default one
client.charges.create_with_payment_method(NewChargePaymentMethod(amount=Decimal("9.95"), payment_method_id=pm_id))
client.charges.create_with_customer(NewChargeCustomer(amount=Decimal("9.95"), customer_id=customer_id))

# Authorise, then capture or void
authorised = client.charges.create_with_token(
    NewChargeToken(amount=Decimal("50.00"), currency="AUD", token=token, capture=False)
)
client.charges.capture(authorised.charge_id, Decimal("45.00"))  # or client.charges.void(authorised.charge_id)

# Refund part of a charge, or all of it
client.charges.refund(charge.charge_id, Decimal("5.00"), comment="Damaged in transit")
client.charges.refund(charge.charge_id)

client.charges.get(charge.charge_id)
page = client.charges.search(ChargeSearch(added_after=datetime(2026, 11, 1, tzinfo=timezone.utc), limit=50))
```

Also `create_with_card_least_cost`, `create_with_bank_account` and `create_with_network_token`.

### Customers and payment methods

```python
customer = client.customers.create_with_token(NewCustomerToken(token=token, email="ann@example.com"))
client.customers.add_payment_method_with_token(customer.customer_id, NewPaymentMethodToken(token=other_token))
client.customers.payment_methods(customer.customer_id)
client.customers.update(customer.customer_id, UpdateCustomer(phone="+61400000000"))
client.customers.search(CustomerSearch(email="ann@example.com"))
client.customers.delete(customer.customer_id)

payment_method = client.payment_methods.create_with_token(NewPaymentMethodToken(token=token))
client.payment_methods.get(payment_method.payment_method_id)
client.payment_methods.delete(payment_method.payment_method_id)
```

Customers and payment methods can also be created from a card, a bank account, a PayTo agreement or a gateway's
token (`create_with_provider_token`, `create_with_single_use_token`); payment methods also from the vault
(`create_with_vault`).

### Subscriptions

```python
subscription = client.subscriptions.create(
    SubscriptionCreate(
        payment_method_id=pm_id,
        amount=Decimal("9.95"),
        currency="AUD",
        interval=SubscriptionInterval.MONTH,
        frequency=1,
    )
)
client.subscriptions.update_status(subscription.subscription_id, SubscriptionStatus.SUSPENDED)
client.subscriptions.delete(subscription.subscription_id)
```

### The rest

```python
client.transfers.create(
    NewTransferGroup(
        provider_id=provider_id,
        group_reference="g1",
        charge_id=charge_id,
        transfers=[NewTransfer(account="acct_1", amount=Decimal("5.00"))],
    )
)
client.vaults.create(NewVault(card_number="4111111111111111", expire_seconds=3600))  # .get, .delete
client.webhook_subscriptions.create(
    NewWebhookSubscription(url="https://shop.example/hooks", types=[WebhookType.TRANSACTION])
)
client.disputes.search()  # .get
client.settlements.search(date(2026, 11, 1), date(2026, 11, 7))
client.info.providers(Decimal("20.00"), "AUD")  # the payment methods a checkout can show
client.version()  # the API's version and region
```

Also `batches` (charge many payment methods at once), `providers` (the account's gateways), `payment_links` and
`tokens`. `info.providers()` also works with only a public key:
`PayfurlClient(None, Environment.SANDBOX, public_key="pub...")`.

## Errors and retries

Every error is a `payfurl.PayfurlError`:

| Exception | When |
| --- | --- |
| `APIError` | The API answered with an error: a decline, a validation error, a conflict, a server error |
| `AuthenticationError` (an `APIError`) | HTTP 401 or 403: a wrong key, or a key that can't call the endpoint |
| `NotFoundError` (an `APIError`) | HTTP 404 |
| `APIConnectionError` | No response: DNS, a refused or dropped connection, TLS |
| `APITimeoutError` (an `APIConnectionError`) | No response within `timeout` |

```python
from payfurl import APIError, ErrorCode

try:
    client.charges.create_with_token(NewChargeToken(amount=Decimal("20.00"), currency="AUD", token=token))
except APIError as e:
    print(e.status_code, e.error_code, e.message, e.gateway_code, e.gateway_message, e.charge_id)
    if e.error_code == ErrorCode.INSUFFICIENT_FUNDS:
        ...
```

`error_code` is payFURL's [error code](https://docs.payfurl.com/errorcodes); `body` is the API's error response.
`is_retryable` says whether the same request may succeed later.

GETs are retried twice by default (`max_retries`) after a connection error, a timeout or a retryable API error,
waiting 0.5 s and then 1 s (`retry_delay`, doubled each time). Nothing else is retried: the API has no idempotency
keys, so a retried charge could charge twice. After a timeout on a charge, look it up (`charges.search` by your
`reference`) before charging again.

## Webhooks

payFURL signs each webhook with the account's webhook signing key: the `X-Payfurl-Signature` header holds base64 of
the body's HMAC-SHA256. Check it against the raw body, before you parse it:

```python
from payfurl import webhooks

event = webhooks.parse(request.body, request.headers.get("X-Payfurl-Signature"), signing_key)
if event["meta"]["type"] == "Transaction":
    charge_id = event["data"]["chargeId"]
```

`parse` raises `webhooks.WebhookSignatureError` when the signature doesn't match; `webhooks.verify` returns a bool.

## Logging

The SDK logs each request at `DEBUG` on the `payfurl` logger: the method, the path, the status and the time. It never
logs a body or a header, so card numbers and keys don't reach your logs.

## Calling an endpoint the SDK has no method for

```python
data = client.request("GET", "/some/path", params={"limit": "10"})
```

`request(method, path, *, json=None, params=None, auth="secret", headers=None)` sends the request with the client's
key, TLS, retries and errors, and returns the response's JSON (`None` for an empty body). `auth` is `"secret"`,
`"public"` (the client's `public_key`) or `None`. It's for advanced use: prefer the typed methods.

## Versions

The SDK follows [semantic versioning](https://semver.org); [CHANGELOG.md](CHANGELOG.md) lists every release. It
supports the Python versions that are not end-of-life.

## Contributing

[CONTRIBUTING.md](CONTRIBUTING.md): development, tests and releases.

## License

MIT
