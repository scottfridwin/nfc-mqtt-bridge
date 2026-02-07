# NFC → MQTT Bridge

Reads NFC tags using PC/SC and publishes them to MQTT.
Designed for Raspberry Pi and Docker.

Disclaimer: This was (almost) entirely by AI.

---
## Requirements (Host)
Install on Raspberry Pi / Linux host:
```bash
sudo apt install pcscd pcsc-tools
sudo systemctl enable --now pcscd
```
Verify:
```bash
pcsc_scan
```
---
## Build & Run
```bash
docker compose build
docker compose up -d
```
---
## Home Assistant Example
```yaml
mqtt:
sensor:
- name: "NFC Tag"
state_topic: "homeassistant/nfc/tag"
```
---
## Supported Architectures
Multi-arch builds supported:
- amd64
- arm64
- arm/v8
Buildx example:
```bash
docker buildx build \
--platform linux/amd64,linux/arm64,linux/arm/v8 \
-t yourrepo/nfc-mqtt . \
--push
```
