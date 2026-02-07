#!/bin/bash
set -e

echo "[INFO] Waiting for pcscd socket..."

for i in {1..15}; do
  if [ -S /run/pcscd/pcscd.comm ]; then
    echo "[INFO] pcscd socket found"
    break
  fi
  sleep 1
done

if [ ! -S /run/pcscd/pcscd.comm ]; then
  echo "[ERROR] pcscd socket not found"
  exit 1
fi

exec python /app/app.py
