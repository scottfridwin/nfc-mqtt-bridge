#!/bin/bash
# Start script for NFC MQTT Bridge inside container

# Start pcscd in the foreground
echo "[INFO] Starting pcscd daemon..."
pcscd -f &

# Wait for pcscd socket
while [ ! -S /var/run/pcscd/pcscd.comm ]; do
    echo "[INFO] Waiting for pcscd socket..."
    sleep 1
done

echo "[INFO] pcscd socket found"
exec python nfc_reader.py
