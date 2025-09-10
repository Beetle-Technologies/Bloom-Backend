#!/bin/bash

echo "Running pre-start script..."

echo "Checking database connection..."
PYTHONPATH=. python ./src/core/initializers/database.py
if [ $? -ne 0 ]; then
    echo "Database connection check failed. Exiting."
    exit 1
fi
echo "Database is ready."

echo "Running migrations..."
alembic upgrade head
if [ $? -ne 0 ]; then
    echo "Migrations failed. Exiting."
    exit 1
fi
echo "Migrations completed successfully."

echo "Loading fixtures..."
PYTHONPATH=. python ./src/core/initializers/fixtures.py
if [ $? -ne 0 ]; then
    echo "Loading fixtures failed. Exiting."
    exit 1
fi
echo "Fixtures loaded successfully."

echo "Pre-start script completed successfully."
