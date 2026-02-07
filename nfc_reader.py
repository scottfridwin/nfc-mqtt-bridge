#!/usr/bin/env python3
import os
import time
import json
import logging
import signal
import threading
import paho.mqtt.client as mqtt
from smartcard.Exceptions import CardConnectionException, NoCardException
from smartcard.scard import (
    SCardEstablishContext,
    SCARD_SCOPE_USER,
    SCardGetStatusChange,
    SCARD_STATE_PRESENT,
)
from smartcard.pcsc.PCSCExceptions import EstablishContextException

# -----------------------
# Logging
# -----------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("nfc")

# -----------------------
# Environment Variables
# -----------------------
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "homeassistant/nfc/tag")
DEVICE_ID = os.getenv("DEVICE_ID", "nfc_reader")

# Home Assistant discovery topics
DISCOVERY_TOPIC = f"homeassistant/sensor/{DEVICE_ID}/uid/config"
STATE_TOPIC = f"homeassistant/sensor/{DEVICE_ID}/uid/state"
AVAILABILITY_TOPIC = f"homeassistant/sensor/{DEVICE_ID}/availability"

# -----------------------
# MQTT Setup
# -----------------------
def setup_mqtt():
    client = mqtt.Client()
    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_start()
    log.info(f"Connected to MQTT broker at {MQTT_HOST}:{MQTT_PORT}")
    return client

# -----------------------
# Home Assistant Discovery
# -----------------------
def publish_discovery(client):
    payload = {
        "name": f"NFC Reader {DEVICE_ID}",
        "unique_id": f"{DEVICE_ID}_uid",
        "state_topic": STATE_TOPIC,
        "availability_topic": AVAILABILITY_TOPIC,
        "icon": "mdi:nfc",
        "device": {
            "identifiers": [DEVICE_ID],
            "name": f"NFC Reader {DEVICE_ID}",
            "manufacturer": "DIY",
            "model": "Raspberry Pi NFC",
        }
    }
    client.publish(DISCOVERY_TOPIC, json.dumps(payload), retain=True)
    client.publish(AVAILABILITY_TOPIC, "online", retain=True)
    log.info("Home Assistant MQTT discovery published")

def set_offline(client):
    client.publish(AVAILABILITY_TOPIC, "offline", retain=True)

# -----------------------
# NFC Reader Event Loop
# -----------------------
def monitor_reader(client):
    try:
        context = SCardEstablishContext(SCARD_SCOPE_USER)
    except EstablishContextException as e:
        log.error(f"Cannot establish PC/SC context: {e}")
        return

    last_uid = None
    reader_state = {}
    while True:
        try:
            # Wait indefinitely for a card present event
            readers_list = pcsc_readers(context)
            if not readers_list:
                time.sleep(2)
                continue

            for reader in readers_list:
                hreader = reader.createConnection()
                # Poll the reader status
                reader_state[reader] = reader_state.get(reader, 0)
                try:
                    hreader.connect()
                    card_present = True
                except NoCardException:
                    card_present = False

                if card_present:
                    uid = hreader.getATR()
                    uid_str = "".join(f"{x:02X}" for x in uid)
                    if uid_str != last_uid:
                        log.info(f"Tag detected: {uid_str}")
                        client.publish(STATE_TOPIC, uid_str, qos=1, retain=False)
                        last_uid = uid_str
                else:
                    last_uid = None

            time.sleep(0.5)
        except CardConnectionException as e:
            log.warning(f"Reader connection error: {e}")
            last_uid = None
            time.sleep(1)
        except Exception as e:
            log.error(f"Unexpected error in monitor loop: {e}")
            time.sleep(2)

# -----------------------
# Signal Handling
# -----------------------
def handle_shutdown(signum, frame):
    log.info("Shutting down NFC reader...")
    set_offline(mqtt_client)
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    exit(0)

signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

# -----------------------
# Main
# -----------------------
if __name__ == "__main__":
    log.info("Starting NFC MQTT Bridge (event-based)")
    mqtt_client = setup_mqtt()
    publish_discovery(mqtt_client)

    # Start NFC monitoring thread
    threading.Thread(target=monitor_reader, args=(mqtt_client,), daemon=True).start()

    # Keep the main thread alive
    while True:
        time.sleep(1)
