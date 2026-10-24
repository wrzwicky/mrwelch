#!/usr/bin/env bash
set -euo pipefail

# Keep dependency installation in the same environment used by the Replit
# Python toolchain and fail if project metadata and the committed lock diverge.
UV_PROJECT_ENVIRONMENT=.pythonlibs uv sync --locked --no-install-project
