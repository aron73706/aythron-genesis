#!/bin/bash

# Ensure we exit on any error
set -e

# Resolve script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$DIR/.."

cd "$ROOT_DIR"

echo "=== Starting Aythron Genesis ==="
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "Installing requirements..."
    .venv/bin/pip install -r requirements.txt
fi

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Starting FastAPI app server on http://localhost:8000..."
python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
