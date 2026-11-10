# payfurl/pythonsdk. `just` lists the recipes.

# Lint, types and the unit tests, as CI runs them (offline: nothing calls an API)
test:
    uv sync --locked
    uv run --no-sync ruff check .
    uv run --no-sync ruff format --check .
    uv run --no-sync mypy
    uv run --no-sync pytest

# Fix what ruff can: imports, formatting
fix:
    uv run ruff check --fix .
    uv run ruff format .

# The sdist and wheel, as the release workflow builds them, into dist/
build:
    uv build

# The integration tests: payfurl/platform's API tests (api.tests) on this checkout, against the API on this machine
# (the platform's `just dev`); args go to pytest
e2e *args:
    #!/usr/bin/env bash
    set -euo pipefail
    sdk=$(pwd)
    platform=${PLATFORM_DIR:-}
    if [ -z "$platform" ]; then
        for candidate in ../platform ../../platform; do
            if [ -f "$candidate/e2e/api-tests/api.tests/conftest.py" ]; then platform=$candidate; break; fi
        done
    fi
    [ -n "$platform" ] && [ -f "$platform/e2e/api-tests/api.tests/conftest.py" ] \
        || { echo "no payfurl/platform checkout at ../platform or ../../platform: set PLATFORM_DIR" >&2; exit 1; }
    cd "$platform" && PYTHONSDK_DIR="$sdk" just e2e api {{args}}
