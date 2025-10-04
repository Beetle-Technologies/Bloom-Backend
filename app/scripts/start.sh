#!/bin/bash
set -e

# Function to handle graceful shutdown
cleanup() {
    echo "Received shutdown signal, stopping uvicorn server gracefully..."
    if [ ! -z "$UVICORN_PID" ]; then
        kill -TERM $UVICORN_PID 2>/dev/null || true
        wait $UVICORN_PID 2>/dev/null || true
    fi
    exit 0
}

# Set up signal handlers for graceful shutdown
trap cleanup SIGINT SIGTERM

# Determine the module to run
if [ -f "./src/main.py" ]; then
    DEFAULT_MODULE_NAME="src.main"
elif [ -f "./main.py" ]; then
    DEFAULT_MODULE_NAME="main"
else
    echo "ERROR: Cannot find main.py in current directory or src/ subdirectory"
    exit 1
fi

# Run pre-start script if it exists
if [ -f "./scripts/pre-start.sh" ]; then
    echo "Running pre-start script..."
    ./scripts/pre-start.sh
fi

# Configure application module
MODULE_NAME=${MODULE_NAME:-$DEFAULT_MODULE_NAME}
VARIABLE_NAME=${VARIABLE_NAME:-app}
export APP_MODULE=${APP_MODULE:-"$MODULE_NAME:$VARIABLE_NAME"}

# Production server configuration
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-80}
LOG_LEVEL=${LOG_LEVEL:-info}

# Worker configuration - optimize for Docker container
# Use 1 worker per CPU core, with a minimum of 1 and maximum of 8
WORKERS=${WORKERS:-$(nproc --all 2>/dev/null || echo "1")}
if [ "$WORKERS" -gt 8 ]; then
    WORKERS=8
fi
if [ "$WORKERS" -lt 1 ]; then
    WORKERS=1
fi

# Worker connections - number of simultaneous connections per worker
WORKER_CONNECTIONS=${WORKER_CONNECTIONS:-1000}

# Worker class - use uvloop for better performance
WORKER_CLASS=${WORKER_CLASS:-uvicorn.workers.UvicornWorker}

# Timeout configuration
TIMEOUT=${TIMEOUT:-30}
KEEPALIVE=${KEEPALIVE:-5}

# Graceful timeout for shutdown
GRACEFUL_TIMEOUT=${GRACEFUL_TIMEOUT:-30}

# Maximum requests per worker (helps with memory leaks)
MAX_REQUESTS=${MAX_REQUESTS:-1000}
MAX_REQUESTS_JITTER=${MAX_REQUESTS_JITTER:-100}

echo "Starting production server..."
echo "App module: $APP_MODULE"
echo "Workers: $WORKERS"
echo "Worker class: $WORKER_CLASS"
echo "Host: $HOST"
echo "Port: $PORT"
echo "Log level: $LOG_LEVEL"
echo "Current directory: $(pwd)"

# Start uvicorn with gunicorn for production
exec uvicorn "$APP_MODULE" \
    --host "$HOST" \
    --port "$PORT" \
    --log-level "$LOG_LEVEL" \
    --workers "$WORKERS" \
    --worker-connections "$WORKER_CONNECTIONS" \
    --timeout-keep-alive "$KEEPALIVE" \
    --access-log \
    --use-colors \
    --loop uvloop \
    --http httptools
