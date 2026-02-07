# syntax=docker/dockerfile:1.7

############################
# Base image
############################
FROM python:3.11-slim

ENV \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_PREFER_BINARY=1

WORKDIR /app

############################
# System dependencies
############################
RUN apt-get update && apt-get install -y --no-install-recommends \
    pcscd \
    libpcsclite1 \
    libpcsclite-dev \
    pcsc-tools \
    libusb-1.0-0 \
    ca-certificates \
    curl \
    gcc \
    pkg-config \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

############################
# Python dependencies (cached)
############################
COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip setuptools wheel && \
    pip install --prefer-binary -r requirements.txt

############################
# Application code
############################
COPY nfc_reader.py .
COPY start.sh .
RUN chmod +x start.sh

############################
# Non-root user (security)
############################
RUN useradd -m appuser
USER appuser

############################
# Startup
############################
ENTRYPOINT ["./start.sh"]
