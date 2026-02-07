# 1. Base image
FROM python:3.9-bullseye AS base

# 2. Install system dependencies in one layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpcsclite1 libpcsclite-dev pcsc-tools \
    libusb-1.0-0 libusb-1.0-0-dev \
    build-essential pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 3. Set working directory
WORKDIR /app

# 4. Copy and install Python dependencies separately for caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
&& pip install --no-cache-dir -r requirements.txt

# 5. Copy application code last to leverage layer caching
COPY nfc_reader.py start.sh .
RUN chmod +x start.sh

# 6. Use non-root user
RUN useradd -m -u 1000 nfcuser
USER nfcuser

CMD ["./start.sh"]
