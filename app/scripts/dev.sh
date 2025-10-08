#!/bin/bash
set -e

UVICORN_PID=""

cleanup() {
    echo "Stopping development servers..."
    if [ ! -z "$UVICORN_PID" ]; then
        kill $UVICORN_PID 2>/dev/null || true
    fi
    job_count=$(jobs -p | wc -l)
    if [ "$job_count" -gt 0 ]; then
        echo "Killing remaining background jobs..."
        kill $(jobs -p) 2>/dev/null || true
    fi
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

if [ -f "./src/main.py" ]; then
    DEFAULT_MODULE_NAME="src.main"
elif [ -f "./main.py" ]; then
    DEFAULT_MODULE_NAME="main"
else
    echo "ERROR: Cannot find main.py in current directory or src/ subdirectory"
    exit 1
fi

if [ -f "./scripts/pre-start.sh" ]; then
    ./scripts/pre-start.sh
fi

MODULE_NAME=${MODULE_NAME:-$DEFAULT_MODULE_NAME}
VARIABLE_NAME=${VARIABLE_NAME:-app}
export APP_MODULE=${APP_MODULE:-"$MODULE_NAME:$VARIABLE_NAME"}

HOST=${HOST:-0.0.0.0}
PORT=${PORT:-3000}
LOG_LEVEL=${LOG_LEVEL:-info}

echo "Starting development servers..."
echo "App module: $APP_MODULE"
echo "Current directory: $(pwd)"


echo "Starting Uvicorn server..."
uvicorn --reload --reload-dir /app/src --host $HOST --port $PORT --log-level $LOG_LEVEL "$APP_MODULE" &
UVICORN_PID=$!
echo "Uvicorn started with PID: $UVICORN_PID"


wait
