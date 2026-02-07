# =========================
# Build stage
# =========================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    swig \
    libpcsclite-dev \
    libusb-1.0-0-dev \
    pkg-config \
    python3-dev \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for caching)
COPY requirements.txt .

# Build wheels
RUN pip install --upgrade pip setuptools wheel \
 && pip wheel --no-cache-dir --no-deps -r requirements.txt


# =========================
# Runtime stage
# =========================
FROM python:3.11-slim

WORKDIR /app

# Install runtime deps only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpcsclite1 \
    pcsc-tools \
 && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder
COPY --from=builder /build /wheels

# Install wheels
RUN pip install --no-cache-dir /wheels/*

# Copy app
COPY nfc_reader.py .
COPY start.sh .

RUN chmod +x start.sh

ENTRYPOINT ["./start.sh"]
