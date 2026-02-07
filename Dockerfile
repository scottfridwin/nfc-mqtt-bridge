FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
libpcsclite1 \
libpcsclite-dev \
pcsc-tools \
&& rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

RUN useradd -m nfcuser
USER nfcuser

ENTRYPOINT ["/app/entrypoint.sh"]
