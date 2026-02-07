FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    pcscd \
    libpcsclite1 \
    libpcsclite-dev \
    pcsc-tools \
    libusb-1.0-0 \
    libusb-1.0-0-dev \
    build-essential \
    pkg-config \
    libssl-dev \
    libffi-dev \
    rustc \
    cargo \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .

# Upgrade pip tools
RUN pip install --upgrade pip setuptools wheel

# Install Python deps (builds pyscard correctly on ARM)
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY nfc_reader.py .
COPY start.sh .

RUN chmod +x start.sh

# Non-root user
RUN useradd -m appuser
USER appuser

CMD ["./start.sh"]
