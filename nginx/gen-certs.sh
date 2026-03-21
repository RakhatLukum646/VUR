#!/usr/bin/env bash
# Generate a self-signed TLS certificate for local development.
# Run once before `docker compose up`:
#   bash nginx/gen-certs.sh
set -euo pipefail

CERT_DIR="$(dirname "$0")/certs"
mkdir -p "$CERT_DIR"

openssl req -x509 -nodes -newkey rsa:2048 \
  -keyout "$CERT_DIR/server.key" \
  -out    "$CERT_DIR/server.crt" \
  -days   365 \
  -subj   "/CN=localhost/O=VUR Dev/C=KZ" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

echo "Certificates written to $CERT_DIR/"
