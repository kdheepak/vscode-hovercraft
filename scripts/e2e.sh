#!/usr/bin/env bash

# Run the VSCode extension tests
export CODE_TESTS_PATH="$(pwd)/out/test"
export CODE_TESTS_WORKSPACE="$(pwd)/testFixture"

echo "Running VSCode extension tests..."
npm run test

echo "Running Python language server tests..."
cd hovercraft
uv sync --extra dev
uv run python -m pytest tests/ -v

echo "All tests completed!"