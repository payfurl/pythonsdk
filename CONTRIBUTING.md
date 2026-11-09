# Contributing

Pull requests are welcome. For a change to what the SDK sends or reads, say which API behaviour it follows.

## Development

You need [uv](https://docs.astral.sh/uv/) and [just](https://just.systems).

```bash
just test    # ruff, mypy --strict and the unit tests, as CI runs them
just fix     # ruff's fixes and formatting
just build   # the sdist and wheel, into dist/
```

The unit tests (`tests/`) send every request to [respx](https://lundberg.github.io/respx/), a fake of httpx, and
never call an API. `tests/test_resources.py` has a case for every endpoint method (method, path, query, body and the
response type) and fails when a public method has none.

The layout:

| Path | What |
| --- | --- |
| `src/payfurl/_client.py` | `PayfurlClient`, `Environment`: URLs, keys, retries, errors, logging, `request()` |
| `src/payfurl/resources.py` | One class per part of the API, one method per endpoint |
| `src/payfurl/models.py` | The request and response models |
| `src/payfurl/errors.py` | The exceptions and `ErrorCode` |
| `src/payfurl/webhooks.py` | Webhook signature checks |

A new endpoint is a method in `resources.py`, its models in `models.py` (requests extend `_Request`, responses
`_Response`), a case in `tests/test_resources.py` and a line in `CHANGELOG.md`.

## Integration tests

payFURL runs the SDK against the API, built from source, before each release. Maintainers with a checkout of the
platform beside this one run `just e2e`.

## Releasing

1. Run the integration tests against the release's commit.
2. Set `version` in `pyproject.toml` and add the version's section to `CHANGELOG.md`; merge to `main`.
3. Tag the merge `vX.Y.Z` and push the tag. The **Release** workflow (`.github/workflows/publish.yml`) runs CI,
   fails if the tag is not on `main`, is not `v` + the version, or has no changelog section, builds the sdist and
   wheel, publishes them to PyPI with Trusted Publishing (no API token; the `pypi` environment), and creates the
   GitHub release from the changelog section.
