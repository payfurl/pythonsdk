from __future__ import annotations

import logging
import time
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum, StrEnum
from importlib.metadata import version
from types import TracebackType
from typing import Any, Literal, TypeVar, cast

import httpx
from pydantic import BaseModel, TypeAdapter

from . import resources
from .errors import APIConnectionError, APIError, APITimeoutError, AuthenticationError, NotFoundError
from .models import ApplicationVersion, RootStatus

__version__ = version("payfurl")

logger = logging.getLogger("payfurl")

T = TypeVar("T")


class Environment(StrEnum):
    """Which payFURL API a client calls. The key's region (its last part, such as `-au`) picks the regional host."""

    #: The API on this machine (https://localhost:5001). TLS isn't verified: it serves a development certificate.
    LOCAL = "local"
    DEVELOPMENT = "development"
    SANDBOX = "sandbox"
    PRODUCTION = "production"


_HOSTS = {
    Environment.LOCAL: "https://localhost:5001",
    Environment.DEVELOPMENT: "https://develop-api{region}.payfurl.com",
    Environment.SANDBOX: "https://sandbox-api{region}.payfurl.com",
    Environment.PRODUCTION: "https://api{region}.payfurl.com",
}
_REGIONS = {"au"}


def _base_url(environment: Environment, key: str) -> str:
    # A key ends in its account's region: sectest...-au. A region without a host of its own uses the global one.
    region = key.rsplit("-", 1)[1].lower() if "-" in key else ""
    return _HOSTS[environment].format(region=f"-{region}" if region in _REGIONS else "")


Auth = Literal["secret", "public"] | None


class PayfurlClient:
    """The payFURL API with one account's keys.

        client = PayfurlClient("sectest...-au", Environment.SANDBOX)
        charge = client.charges.create_with_token(NewChargeToken(amount=Decimal("20.00"), currency="AUD", token=token))

    The secret key calls every endpoint. A public key (`public_key=`) is needed only by `request(auth="public")`;
    `info.providers()` takes either. Make one client per account and reuse it: it keeps connections open. Close it
    with `close()`, or use it as a context manager.

    GETs are retried `max_retries` times after a connection error, a timeout or a retryable API error, waiting
    `retry_delay` seconds and doubling the wait each time. Nothing else is retried: the API has no idempotency keys,
    so a retried charge could charge twice.

    `http_client` sends the requests in place of the client's own (for proxies or event hooks); its TLS settings are
    used as they are. `timeout` applies to every request either way.
    """

    def __init__(
        self,
        secret_key: str | None,
        environment: Environment | str,
        *,
        public_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 60.0,
        max_retries: int = 2,
        retry_delay: float = 0.5,
        http_client: httpx.Client | None = None,
    ) -> None:
        if not (secret_key or "").strip() and not (public_key or "").strip():
            raise ValueError("A payFURL secret key or public key is needed")
        try:
            environment = Environment(str(environment).lower())
        except ValueError:
            names = ", ".join(e.value for e in Environment)
            raise ValueError(f"Unknown payFURL environment {environment!r}: use {names}") from None
        self.secret_key = secret_key or None
        self.public_key = public_key or None
        self.environment = environment
        self.base_url = (base_url or _base_url(environment, self.secret_key or self.public_key or "")).rstrip("/")
        self.timeout = timeout
        self.max_retries = max(0, max_retries)
        self.retry_delay = retry_delay
        self._owns_http = http_client is None
        # TLS is verified unless the client is for the API on this machine, and never changed on a caller's client.
        self._http = http_client or httpx.Client(verify=environment is not Environment.LOCAL)

        self.batches = resources.Batches(self)
        self.charges = resources.Charges(self)
        self.customers = resources.Customers(self)
        self.disputes = resources.Disputes(self)
        self.info = resources.Info(self)
        self.payment_links = resources.PaymentLinks(self)
        self.payment_methods = resources.PaymentMethods(self)
        self.providers = resources.Providers(self)
        self.settlements = resources.Settlements(self)
        self.subscriptions = resources.Subscriptions(self)
        self.tokens = resources.Tokens(self)
        self.transfers = resources.Transfers(self)
        self.vaults = resources.Vaults(self)
        self.webhook_subscriptions = resources.WebhookSubscriptions(self)

    def root(self) -> RootStatus:
        """`GET /`: whether the API is up. Needs no key."""
        return self._call("GET", "/", RootStatus, auth=None)

    def version(self) -> ApplicationVersion:
        """`GET /version`: the API's version and region."""
        return self._call("GET", "/version", ApplicationVersion, auth=None)

    def request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: dict[str, str] | None = None,
        auth: Auth = "secret",
        headers: dict[str, str] | None = None,
    ) -> Any:
        """Advanced: calls an endpoint the SDK has no method for, with the client's keys, TLS, retries and errors.

        Returns the response's JSON, decoded as `json.loads` does (`None` for an empty body), and raises the same
        errors as the other methods. `auth` picks the key header: `"secret"`, `"public"` (needs `public_key`) or
        `None`. Prefer the typed methods: an endpoint called this way may change without notice.
        """
        response = self._send(method, path, json=json, params=params, auth=auth, headers=headers)
        return response.json() if response.content.strip() else None

    def close(self) -> None:
        """Closes the client's connections. A caller's `http_client` is left open."""
        if self._owns_http:
            self._http.close()

    def __enter__(self) -> PayfurlClient:
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None
    ) -> None:
        self.close()

    def _call(
        self,
        method: str,
        path: str,
        response_type: type[T],
        *,
        body: BaseModel | dict[str, Any] | None = None,
        query: BaseModel | dict[str, Any] | None = None,
        auth: Auth = "secret",
        headers: dict[str, str] | None = None,
    ) -> T:
        if isinstance(body, BaseModel):
            json: Any = body.model_dump(mode="json", by_alias=True, exclude_none=True)
        else:
            json = None if body is None else {k: _json_value(v) for k, v in body.items() if v is not None}
        params = _query(query.model_dump(by_alias=True, exclude_none=True) if isinstance(query, BaseModel) else query)
        response = self._send(method, path, json=json, params=params, auth=auth, headers=headers)
        return cast(T, _adapter(response_type).validate_json(response.content))

    def _send(
        self,
        method: str,
        path: str,
        *,
        json: Any,
        params: dict[str, str] | None,
        auth: Auth,
        headers: dict[str, str] | None,
    ) -> httpx.Response:
        method = method.upper()
        sent = {"Accept": "application/json", "User-Agent": f"payfurl-python/{__version__}", **(headers or {})}
        if auth is not None:
            key = self.secret_key if auth == "secret" else self.public_key
            if key is None:
                raise ValueError(f"This client has no {auth} key")
            sent["x-secretkey" if auth == "secret" else "x-publickey"] = key

        # Only reads are retried: a second charge POST could charge twice.
        retries = self.max_retries if method == "GET" else 0
        attempt = 0
        while True:
            start = time.monotonic()
            try:
                try:
                    response = self._http.request(
                        method, self.base_url + path, json=json, params=params, headers=sent, timeout=self.timeout
                    )
                except httpx.TimeoutException as e:
                    raise APITimeoutError(f"{method} {path} timed out after {self.timeout} s") from e
                except httpx.TransportError as e:
                    raise APIConnectionError(f"{method} {path} failed: {e}") from e
                # Never the body or headers: they hold card numbers and keys.
                logger.debug(
                    "%s %s: HTTP %s in %.0f ms", method, path, response.status_code, (time.monotonic() - start) * 1000
                )
                if response.is_success:
                    return response
                raise _error(response)
            except (APIConnectionError, APIError) as e:
                if attempt >= retries or (isinstance(e, APIError) and not e.is_retryable):
                    raise
                logger.debug("%s %s: retrying after %s", method, path, e)
                time.sleep(self.retry_delay * 2**attempt)
                attempt += 1


def _error(response: httpx.Response) -> APIError:
    try:
        body: Any = response.json()
    except ValueError:
        body = response.text.strip() or None
    if isinstance(body, dict) and isinstance(body.get("message"), str):
        message = body["message"]
    elif isinstance(body, str) and body:
        # Some endpoints answer with a plain message, and a proxy with HTML.
        message = body[:500]
    else:
        message = f"HTTP {response.status_code} from the payFURL API"
    status = response.status_code
    cls = AuthenticationError if status in (401, 403) else NotFoundError if status == 404 else APIError
    return cls(message, status_code=status, body=body)


def _json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, Enum):
        return value.value
    return value


def _query(values: dict[str, Any] | None) -> dict[str, str] | None:
    """Query parameters as the API's model binding reads them; `None`s left out."""
    if not values:
        return None
    query = {}
    for name, value in values.items():
        if value is None:
            continue
        if isinstance(value, bool):
            query[name] = "true" if value else "false"
        elif isinstance(value, Decimal):
            query[name] = format(value, "f")  # never an exponent: 1E+2
        elif isinstance(value, datetime):
            # A naive datetime is local time, as datetime.astimezone() takes it.
            query[name] = value.astimezone(UTC).isoformat().replace("+00:00", "Z")
        elif isinstance(value, date):
            query[name] = value.isoformat()
        elif isinstance(value, Enum):
            query[name] = str(value.value)
        else:
            query[name] = str(value)
    return query


_adapters: dict[Any, TypeAdapter[Any]] = {}


def _adapter(response_type: Any) -> TypeAdapter[Any]:
    if response_type not in _adapters:
        _adapters[response_type] = TypeAdapter(response_type)
    return _adapters[response_type]
