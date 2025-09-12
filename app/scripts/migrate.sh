#!/bin/bash

# Script to handle Alembic migrations

if [ "$1" == "create" ]; then
    if [ -z "$2" ]; then
        echo "Usage: $0 create <message>"
        exit 1
    fi
    echo "Creating migration with message: $2"
    alembic revision --autogenerate -m "$2"
elif [ "$1" == "up" ]; then
    echo "Upgrading to head"
    alembic upgrade head
elif [ "$1" == "down" ]; then
    echo "Downgrading to head"
    alembic downgrade head
else
    echo "Usage: $0 {create <message>|up|down}"
    exit 1
fi
