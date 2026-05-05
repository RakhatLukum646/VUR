#!/bin/sh
# Generate a self-signed TLS certificate for local development.
#
# Manual usage (run once before `docker compose up`):
#   bash nginx/gen-certs.sh
#
# The docker compose tls-init service calls this automatically on first run.
# To force regeneration:
#   FORCE=1 bash nginx/gen-certs.sh
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CERT_DIR="${CERT_DIR_OVERRIDE:-"$SCRIPT_DIR/certs"}"
mkdir -p "$CERT_DIR"

if [ -f "$CERT_DIR/server.crt" ] && [ -f "$CERT_DIR/server.key" ] && [ "${FORCE:-0}" = "0" ]; then
    echo "Certificates already exist at $CERT_DIR/ — skipping. Set FORCE=1 to regenerate."
    exit 0
fi

openssl req -x509 -nodes -newkey rsa:2048 \
    -keyout "$CERT_DIR/server.key" \
    -out    "$CERT_DIR/server.crt" \
    -days   365 \
    -subj   "/CN=localhost/O=VUR Dev/C=KZ" \
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

echo "Certificates written to $CERT_DIR/"
