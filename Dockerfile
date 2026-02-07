# Use a small Python image
FROM python:3.11-slim

# Install dependencies for PCSC client
RUN apt-get update && apt-get install -y \
    libpcsclite1 \
    libpcsclite-dev \
    pcsc-tools \
    libusb-1.0-0 \
    libusb-1.0-0-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY nfc_reader.py .
COPY start.sh .
RUN chmod +x start.sh

# Use non-root user for running app
RUN useradd -m -u 1000 nfcuser
USER nfcuser

CMD ["./start.sh"]
