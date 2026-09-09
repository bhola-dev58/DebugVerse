#!/usr/bin/env bash
set -e

echo "================================================================"
echo "  DebugVerse — Full System Design & API Test Suite"
echo "================================================================"
echo ""

export PYTHONPATH=.
./venv/bin/pytest tests/ -v --tb=short

echo ""
echo "================================================================"
echo "  ✓ All System Design & API Tests Passed Successfully!"
echo "================================================================"
