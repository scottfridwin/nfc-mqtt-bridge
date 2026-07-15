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

## MQTT Password Configuration
The bridge supports either:
- `MQTT_PASSWORD`
- `MQTT_PASSWORD_FILE`

If both are set, `MQTT_PASSWORD` wins.

### Docker Secrets (recommended)
Create a local secret file:
```bash
mkdir -p .secrets
printf '%s' 'your-mqtt-password' > .secrets/mqtt_password.txt
chmod 600 .secrets/mqtt_password.txt
```

The included compose file already maps this secret and sets:
```yaml
MQTT_PASSWORD_FILE: /run/secrets/mqtt_password
```

### Direct Environment Variable
If you do not want to use Docker secrets, set:
```yaml
MQTT_PASSWORD: your-mqtt-password
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
