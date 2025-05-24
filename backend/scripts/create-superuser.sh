#!/bin/bash

# AI Meeting Assistant - Create Superuser Wrapper
# This script provides a convenient way to create superusers

set -e

cd "$(dirname "$0")/.."

echo "🚀 AI Meeting Assistant - Superuser Management"
echo "=============================================="

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "❌ UV is not installed. Please install UV first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Run the Python script with uv
uv run python scripts/create_superuser.py "$@" 