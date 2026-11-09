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

# The integration tests, in payfurl/platform, against this checkout and an API built from source (Docker); args go to pytest
e2e *args:
    #!/usr/bin/env bash
    set -euo pipefail
    sdk=$(pwd)
    platform=${PLATFORM_DIR:-}
    if [ -z "$platform" ]; then
        for candidate in ../platform ../../platform; do
            if [ -f "$candidate/e2e/api-tests/pythonsdk/docker-compose.yml" ]; then platform=$candidate; break; fi
        done
    fi
    [ -n "$platform" ] && [ -f "$platform/e2e/api-tests/pythonsdk/docker-compose.yml" ] \
        || { echo "no payfurl/platform checkout at ../platform or ../../platform: set PLATFORM_DIR" >&2; exit 1; }
    cd "$platform" && PYTHONSDK_DIR="$sdk" just e2e pythonsdk {{args}}
