#!/bin/sh

echo "Running database seed script inside the container..."

cd /server || exit

PYTHONPATH=/ python -m server.app.seed

echo "Database seeding process completed!"
