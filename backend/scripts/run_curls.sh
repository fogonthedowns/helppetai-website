#!/usr/bin/env bash
set -euo pipefail

# Simple runner for curl-based integration tests

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TESTS_FILE="$ROOT_DIR/tests/curls.txt"

if [ ! -f "$TESTS_FILE" ]; then
  echo "❌ tests/curls.txt not found at $TESTS_FILE"
  exit 1
fi

echo "🔐 Setting up test data and executing curl sequence..."

# Setup test database with admin user
cd "$ROOT_DIR"
python scripts/setup_test_data.py > /dev/null 2>&1

# Check if server is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
  echo "❌ Test server not running. Start with: make run-test"
  exit 1
fi

echo "✅ Test server is running, executing curls..."

# Create a temporary file to capture errors
ERROR_LOG=$(mktemp)
trap 'rm -f "$ERROR_LOG"' EXIT

# Execute the curl sequence and capture any errors
if ! source "$TESTS_FILE" 2>"$ERROR_LOG"; then
  echo "❌ Integration test failed!"
  if [ -s "$ERROR_LOG" ]; then
    echo "Error details:"
    cat "$ERROR_LOG"
  fi
  exit 1
fi

# Show any captured output
if [ -s "$ERROR_LOG" ]; then
  echo "⚠️  Test warnings/output:"
  cat "$ERROR_LOG"
fi

echo "✅ Curl integration sequence completed"

