# Use slim Python image for small size
FROM python:3.11-slim

# Install dependencies for PCSC and building pyscard
RUN apt-get update && apt-get install -y \
    pcscd \
    libpcsclite1 \
    libpcsclite-dev \
    pcsc-tools \
    libusb-1.0-0 \
    libusb-1.0-0-dev \
    build-essential \
    pkg-config \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy application files
COPY nfc_reader.py start.sh requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# Make startup script executable
RUN chmod +x start.sh

# Use non-root user for safety
RUN useradd -m -u 1000 nfcuser && chown -R nfcuser:nfcuser /app
USER nfcuser

# Entrypoint
CMD ["./start.sh"]
