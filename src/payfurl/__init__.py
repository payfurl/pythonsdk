"""payFURL's Python SDK: the public REST API with an account's secret key.

from payfurl import PayfurlClient, Environment
from payfurl.models import NewChargeToken

client = PayfurlClient("sectest...-au", Environment.SANDBOX)
charge = client.charges.create_with_token(NewChargeToken(amount=Decimal("20.00"), currency="AUD", token=token))
"""

from . import models, webhooks
from ._client import Environment, PayfurlClient, __version__
from .errors import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AuthenticationError,
    ErrorCode,
    NotFoundError,
    PayfurlError,
)

__all__ = [
    "APIConnectionError",
    "APIError",
    "APITimeoutError",
    "AuthenticationError",
    "Environment",
    "ErrorCode",
    "NotFoundError",
    "PayfurlClient",
    "PayfurlError",
    "__version__",
    "models",
    "webhooks",
]
