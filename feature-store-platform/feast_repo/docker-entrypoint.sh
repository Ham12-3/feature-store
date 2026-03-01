#!/bin/sh
set -e

echo "==> Registering feature definitions in shared registry..."
feast apply

echo "==> Starting Feast feature server on :6566..."
exec feast serve -h 0.0.0.0 -p 6566
