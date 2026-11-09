"""Checks that a webhook came from payFURL.

payFURL signs each webhook's body with the account's webhook signing key (the portal's Webhook Secret Key) and sends
the signature in the `X-Payfurl-Signature` header: base64 of the body's HMAC-SHA256. Check it against the raw body,
before parsing it:

    event = payfurl.webhooks.parse(request.body, request.headers.get("X-Payfurl-Signature"), signing_key)
    if event["meta"]["type"] == "Transaction":
        charge_id = event["data"]["chargeId"]
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from typing import Any

from .errors import PayfurlError


class WebhookSignatureError(PayfurlError):
    """The webhook's signature doesn't match its body, or the body isn't JSON: it isn't from payFURL."""


def _bytes(value: str | bytes) -> bytes:
    return value.encode() if isinstance(value, str) else value


def verify(body: str | bytes, signature: str | None, signing_key: str) -> bool:
    """Whether `signature` is the body's, compared in constant time."""
    if not signature or not signing_key:
        return False
    expected = base64.b64encode(hmac.new(_bytes(signing_key), _bytes(body), hashlib.sha256).digest())
    return hmac.compare_digest(expected, _bytes(signature.strip()))


def parse(body: str | bytes, signature: str | None, signing_key: str) -> dict[str, Any]:
    """The webhook's JSON (`data` and `meta`), once its signature checks out.

    Raises `WebhookSignatureError` when the signature doesn't match the body or the body isn't a JSON object.
    """
    if not verify(body, signature, signing_key):
        raise WebhookSignatureError("The webhook's signature does not match its body: it is not from payFURL")
    try:
        event = json.loads(body)
    except ValueError as e:
        raise WebhookSignatureError("The webhook's body is not JSON") from e
    if not isinstance(event, dict):
        raise WebhookSignatureError("The webhook's body is not a JSON object")
    return event
