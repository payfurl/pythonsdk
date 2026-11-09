# Changelog

Every release of `payfurl` on PyPI. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-11-09

The first release.

### Added

- `PayfurlClient(secret_key, environment)`, with the API's parts as attributes: `batches`, `charges`, `customers`,
  `disputes`, `info`, `payment_links`, `payment_methods`, `providers`, `settlements`, `subscriptions`, `tokens`,
  `transfers`, `vaults` and `webhook_subscriptions`, plus `root()` and `version()`. It covers every public endpoint
  that takes the secret key, and `GET /info/providers`.
- The host from the environment and the key's region, or `base_url`. TLS is verified, except for
  `Environment.LOCAL`.
- Pydantic models for every request and response, with `Decimal` amounts.
- Errors: `PayfurlError`, `APIError` (with the payFURL error code, `ErrorCode`), `AuthenticationError`,
  `NotFoundError`, `APIConnectionError` and `APITimeoutError`.
- Retries for GETs after connection errors, timeouts and retryable API errors.
- `payfurl.webhooks.verify` and `parse`: webhook signature checks in constant time.
- `client.request()`, for an endpoint the SDK has no method for.
- Logging on the `payfurl` logger, with no bodies or headers.
