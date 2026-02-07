#!/bin/bash

# Wait for host pcscd socket
SOCKET="/run/pcscd/pcscd.comm"
while [ ! -S "$SOCKET" ]; do
    echo "[INFO] Waiting for pcscd socket..."
    sleep 2
done

echo "[INFO] pcscd socket found. Starting NFC Reader..."
exec python /app/nfc_reader.py
