import json
import logging
from collections.abc import Iterator
from decimal import Decimal
from typing import Any

import httpx
import pytest
import respx

import payfurl
from payfurl import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AuthenticationError,
    Environment,
    ErrorCode,
    NotFoundError,
    PayfurlClient,
)
from payfurl.models import ChargeData, NewChargeCard, TransactionStatus

KEY = "sectest0123456789abcdef-au"
URL = "https://sandbox-api-au.payfurl.com"


@pytest.fixture
def api() -> Iterator[respx.MockRouter]:
    with respx.mock(base_url=URL, assert_all_called=False) as router:
        yield router


@pytest.fixture
def client() -> PayfurlClient:
    return PayfurlClient(KEY, Environment.SANDBOX, retry_delay=0)


@pytest.mark.parametrize(
    ("environment", "key", "url"),
    [
        ("local", KEY, "https://localhost:5001"),
        ("development", KEY, "https://develop-api-au.payfurl.com"),
        ("sandbox", KEY, "https://sandbox-api-au.payfurl.com"),
        ("production", "seclive0123-au", "https://api-au.payfurl.com"),
        ("PRODUCTION", "seclive0123-AU", "https://api-au.payfurl.com"),
        ("production", "seclive0123-us", "https://api.payfurl.com"),
        ("sandbox", "sectest0123", "https://sandbox-api.payfurl.com"),
        (Environment.DEVELOPMENT, "sectest0123-xx", "https://develop-api.payfurl.com"),
    ],
)
def test_base_url_from_environment_and_key_region(environment: str, key: str, url: str) -> None:
    assert PayfurlClient(key, environment).base_url == url


def test_base_url_option_wins() -> None:
    assert PayfurlClient(KEY, "local", base_url="https://api:5001/").base_url == "https://api:5001"


def test_rejects_no_key_and_unknown_environment() -> None:
    with pytest.raises(ValueError, match="key"):
        PayfurlClient(" ", "sandbox")
    with pytest.raises(ValueError, match="staging"):
        PayfurlClient(KEY, "staging")


def test_tls_is_verified_except_local() -> None:
    def verifies(client: PayfurlClient) -> bool:
        ssl = client._http._transport._pool._ssl_context  # type: ignore[attr-defined]
        return bool(ssl.check_hostname)

    assert verifies(PayfurlClient(KEY, "sandbox"))
    assert verifies(PayfurlClient(KEY, "production"))
    assert not verifies(PayfurlClient(KEY, "local"))


def test_a_callers_http_client_is_used_and_left_open(api: respx.MockRouter) -> None:
    api.get("/charge/ch1").respond(json={"chargeId": "ch1"})
    http = httpx.Client()
    with PayfurlClient(KEY, "sandbox", http_client=http) as client:
        assert client.charges.get("ch1").charge_id == "ch1"
    assert not http.is_closed


def test_headers(api: respx.MockRouter, client: PayfurlClient) -> None:
    route = api.post("/charge/card").respond(json={})
    client.charges.create_with_card(NewChargeCard(amount=Decimal(1), provider_id="p"))
    headers = route.calls.last.request.headers
    assert headers["x-secretkey"] == KEY
    assert "x-publickey" not in headers
    assert headers["user-agent"] == f"payfurl-python/{payfurl.__version__}"
    assert headers["accept"] == "application/json"
    assert headers["content-type"] == "application/json"


def test_body_is_camel_case_without_nones_and_amounts_are_numbers(api: respx.MockRouter, client: PayfurlClient) -> None:
    route = api.post("/charge/card").respond(json={})
    client.charges.create_with_card(
        NewChargeCard(
            amount=Decimal("20.10"),
            provider_id="p1",
            capture=False,
            three_ds_notification_url="https://shop/3ds",
            metadata={"order": "1"},
        )
    )
    body = route.calls.last.request.content
    assert json.loads(body) == {
        "amount": 20.1,
        "providerId": "p1",
        "capture": False,
        "threeDSNotificationUrl": "https://shop/3ds",
        "metadata": {"order": "1"},
    }
    assert b'"amount":20.1' in body.replace(b" ", b"")


def test_request_models_reject_unknown_fields() -> None:
    with pytest.raises(ValueError, match="amonut"):
        NewChargeCard(amount=Decimal(1), provider_id="p", amonut=2)  # type: ignore[call-arg]


def test_response_parsing_keeps_unknown_values(api: respx.MockRouter, client: PayfurlClient) -> None:
    api.get("/charge/ch1").respond(
        content=b'{"chargeId":"ch1","amount":20.10,"status":"SUCCESS","dateAdded":"2026-11-09T01:02:03Z",'
        b'"refunds":[{"amount":0.10}],"newField":{"a":1}}'
    )
    charge = client.charges.get("ch1")
    assert charge.amount == Decimal("20.10")
    assert charge.status is TransactionStatus.SUCCESS
    assert charge.date_added is not None and charge.date_added.year == 2026
    assert charge.refunds is not None and charge.refunds[0].amount == Decimal("0.10")
    assert charge.model_extra == {"newField": {"a": 1}}

    api.get("/charge/ch2").respond(json={"status": "SOMETHING_NEW"})
    assert client.charges.get("ch2").status == "SOMETHING_NEW"


def test_ids_are_escaped_and_never_empty(api: respx.MockRouter, client: PayfurlClient) -> None:
    route = api.get(url__regex=r"/charge/a%2Fb%3F").respond(json={})
    client.charges.get("a/b?")
    assert route.called
    with pytest.raises(ValueError, match="charge_id"):
        client.charges.get(" ")


@pytest.mark.parametrize(
    ("status", "body", "error", "code", "retryable"),
    [
        (400, {"message": "Invalid card number", "code": 5, "isRetryable": False}, APIError, 5, False),
        (401, {"message": "Invalid key"}, AuthenticationError, None, False),
        (403, {"message": "Forbidden"}, AuthenticationError, None, False),
        (404, {"message": "No charge", "code": 50}, NotFoundError, 50, False),
        (409, {"message": "Busy", "isRetryable": True}, APIError, None, True),
        (502, "<html>bad gateway</html>", APIError, None, True),
        (500, None, APIError, None, True),
    ],
)
def test_errors(
    api: respx.MockRouter,
    status: int,
    body: dict[str, Any] | str | None,
    error: type[APIError],
    code: int | None,
    retryable: bool,
) -> None:
    client = PayfurlClient(KEY, "sandbox", max_retries=0)
    if isinstance(body, str):
        api.post("/charge/card").respond(status, text=body)
    elif body is None:
        api.post("/charge/card").respond(status)
    else:
        api.post("/charge/card").respond(status, json=body)
    with pytest.raises(error) as raised:
        client.charges.create_with_card(NewChargeCard(amount=Decimal(1), provider_id="p"))
    e = raised.value
    assert type(e) is error
    assert e.status_code == status
    assert e.error_code == code
    assert e.is_retryable is retryable
    assert e.body == (body if body else None)
    assert str(status) in str(e)


def test_error_fields() -> None:
    e = APIError(
        "Declined",
        status_code=400,
        body={
            "message": "Declined",
            "code": 15,
            "type": "https://docs.payfurl.com/errorcodes#15",
            "gatewayCode": "51",
            "gatewayMessage": "Insufficient funds",
            "chargeId": "ch1",
            "details": {"amount": "too much"},
            "resource": "charge",
            "traceId": "t1",
        },
    )
    assert e.error_code == ErrorCode.INSUFFICIENT_FUNDS
    assert (e.gateway_code, e.gateway_message, e.charge_id, e.trace_id) == ("51", "Insufficient funds", "ch1", "t1")
    assert e.details == {"amount": "too much"}
    assert e.type == "https://docs.payfurl.com/errorcodes#15"
    assert e.resource == "charge"


def test_gets_are_retried(api: respx.MockRouter, client: PayfurlClient) -> None:
    route = api.get("/charge/ch1")
    route.side_effect = [
        httpx.ConnectError("refused"),
        httpx.Response(503, json={"message": "later", "isRetryable": True}),
        httpx.Response(200, json={"chargeId": "ch1"}),
    ]
    assert client.charges.get("ch1").charge_id == "ch1"
    assert route.call_count == 3


def test_gets_give_up_after_max_retries(api: respx.MockRouter, client: PayfurlClient) -> None:
    route = api.get("/charge/ch1").respond(503)
    with pytest.raises(APIError):
        client.charges.get("ch1")
    assert route.call_count == 3


def test_errors_that_are_not_retryable_are_not_retried(api: respx.MockRouter, client: PayfurlClient) -> None:
    route = api.get("/charge/ch1").respond(400, json={"message": "bad", "isRetryable": False})
    with pytest.raises(APIError):
        client.charges.get("ch1")
    assert route.call_count == 1


def test_posts_and_deletes_are_never_retried(api: respx.MockRouter, client: PayfurlClient) -> None:
    post = api.post("/charge/card").respond(503)
    delete = api.delete("/charge/ch1").mock(side_effect=httpx.ConnectError("refused"))
    with pytest.raises(APIError):
        client.charges.create_with_card(NewChargeCard(amount=Decimal(1), provider_id="p"))
    with pytest.raises(APIConnectionError):
        client.charges.refund("ch1")
    assert post.call_count == 1
    assert delete.call_count == 1


def test_timeouts_and_connection_errors(api: respx.MockRouter) -> None:
    client = PayfurlClient(KEY, "sandbox", max_retries=0, timeout=3)
    api.get("/charge/ch1").mock(side_effect=httpx.ReadTimeout("slow"))
    api.get("/charge/ch2").mock(side_effect=httpx.ConnectError("refused"))
    with pytest.raises(APITimeoutError, match="3"):
        client.charges.get("ch1")
    with pytest.raises(APIConnectionError) as raised:
        client.charges.get("ch2")
    assert not isinstance(raised.value, APITimeoutError)


def test_timeout_is_sent_with_each_request(api: respx.MockRouter) -> None:
    route = api.get("/charge/ch1").respond(json={})
    PayfurlClient(KEY, "sandbox", timeout=7).charges.get("ch1")
    assert route.calls.last.request.extensions["timeout"] == {"connect": 7, "read": 7, "write": 7, "pool": 7}


def test_logs_never_hold_bodies_or_keys(
    api: respx.MockRouter, client: PayfurlClient, caplog: pytest.LogCaptureFixture
) -> None:
    api.post("/charge/card").respond(json={"chargeId": "ch1", "paymentInformation": {"cardNumber": "4111"}})
    with caplog.at_level(logging.DEBUG, logger="payfurl"):
        client.charges.create_with_card(
            NewChargeCard.model_validate(
                {
                    "amount": 1,
                    "providerId": "p",
                    "paymentInformation": {
                        "cardNumber": "4111111111111111",
                        "expiryDate": "12/30",
                        "ccv": "123",
                    },
                }
            )
        )
    assert "POST /charge/card: HTTP 200" in caplog.text
    for secret in ("4111", "123", KEY):
        assert secret not in caplog.text


def test_request_escape_hatch(api: respx.MockRouter) -> None:
    client = PayfurlClient(KEY, "sandbox", public_key="pubtest0123-au")
    secret = api.get("/info").respond(json={"a": 1.5})
    public = api.post("/token/card").respond(json={"tokenId": "t1"})
    anonymous = api.get("/").respond(204)
    assert client.request("get", "/info", params={"x": "1"}) == {"a": 1.5}
    assert secret.calls.last.request.headers["x-secretkey"] == KEY
    assert secret.calls.last.request.url.params["x"] == "1"
    assert client.request("POST", "/token/card", json={"cardNumber": "4111"}, auth="public", headers={"a": "b"}) == {
        "tokenId": "t1"
    }
    request = public.calls.last.request
    assert request.headers["x-publickey"] == "pubtest0123-au"
    assert request.headers["a"] == "b"
    assert "x-secretkey" not in request.headers
    assert client.request("GET", "/", auth=None) is None
    assert "x-secretkey" not in anonymous.calls.last.request.headers


def test_request_without_the_key_it_needs(client: PayfurlClient) -> None:
    with pytest.raises(ValueError, match="public"):
        client.request("GET", "/x", auth="public")


def test_root_and_version_need_no_key(api: respx.MockRouter, client: PayfurlClient) -> None:
    root = api.get("/").respond(json={"status": "OK"})
    version = api.get("/version").respond(json={"version": "1.2.3", "region": "au"})
    assert client.root().model_extra is not None
    assert client.version().version == "1.2.3"
    assert "x-secretkey" not in root.calls.last.request.headers
    assert "x-secretkey" not in version.calls.last.request.headers


def test_charge_data_round_trips_as_a_dict() -> None:
    charge = ChargeData.model_validate({"chargeId": "ch1", "amount": 1})
    assert charge.model_dump(by_alias=True, exclude_none=True, mode="json") == {"chargeId": "ch1", "amount": 1.0}
