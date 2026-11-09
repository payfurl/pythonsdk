import base64
import hashlib
import hmac

import pytest

from payfurl import PayfurlError, webhooks
from payfurl.webhooks import WebhookSignatureError

KEY = "whsec-0123"
BODY = '{"data":{"chargeId":"ch1","amount":20.5},"meta":{"type":"Transaction"}}'


def sign(body: str, key: str = KEY) -> str:
    """As webhooks-sender signs (SignatureGenerator.ComputeSignature): base64 of HMAC-SHA256 over the UTF-8 body."""
    return base64.b64encode(hmac.new(key.encode(), body.encode(), hashlib.sha256).digest()).decode()


def test_a_known_signature() -> None:
    # From `printf '{}' | openssl dgst -sha256 -hmac key -binary | base64`: a change to how the signature is
    # computed can't pass by changing sign() with it.
    assert sign("{}", "key") == "p3dyTZQ+tI3Gm8qKSm1XoE2z+ex+HeTlgehgJlvfMDI="
    assert webhooks.verify("{}", "p3dyTZQ+tI3Gm8qKSm1XoE2z+ex+HeTlgehgJlvfMDI=", "key")


def test_verify() -> None:
    assert webhooks.verify(BODY, sign(BODY), KEY)
    assert webhooks.verify(BODY.encode(), f" {sign(BODY)}\n", KEY)
    assert not webhooks.verify(BODY + " ", sign(BODY), KEY)
    assert not webhooks.verify(BODY, sign(BODY, "other"), KEY)
    assert not webhooks.verify(BODY, None, KEY)
    assert not webhooks.verify(BODY, "", KEY)
    assert not webhooks.verify(BODY, sign(BODY), "")


def test_parse() -> None:
    event = webhooks.parse(BODY, sign(BODY), KEY)
    assert event["meta"]["type"] == "Transaction"
    assert event["data"]["chargeId"] == "ch1"


def test_parse_rejects_a_forged_or_broken_body() -> None:
    with pytest.raises(WebhookSignatureError, match="not from payFURL"):
        webhooks.parse(BODY, sign("{}"), KEY)
    with pytest.raises(PayfurlError, match="not JSON"):
        webhooks.parse("not json", sign("not json"), KEY)
    with pytest.raises(WebhookSignatureError, match="object"):
        webhooks.parse("[1]", sign("[1]"), KEY)
