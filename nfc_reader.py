#!/usr/bin/env python3

import os
import time
import json
import socket
import logging
import threading

import paho.mqtt.client as mqtt

from smartcard.System import readers
from smartcard.util import toHexString
from smartcard.CardMonitoring import CardMonitor, CardObserver
from smartcard.Exceptions import NoCardException


# ==================================================
# Configuration
# ==================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

MQTT_HOST = os.getenv("MQTT_HOST")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "homeassistant/nfc/tag")

DEVICE_ID = socket.gethostname()
DEVICE_NAME = os.getenv("DEVICE_NAME", "NFC Kiosk Reader")

DISCOVERY_TOPIC = f"homeassistant/sensor/{DEVICE_ID}/config"
STATE_TOPIC = MQTT_TOPIC


# ==================================================
# Logging
# ==================================================

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

log = logging.getLogger("nfc")


# ==================================================
# MQTT
# ==================================================

mqtt_client = None


def setup_mqtt():
    global mqtt_client

    client = mqtt.Client(
        client_id=f"nfc-{DEVICE_ID}",
        protocol=mqtt.MQTTv311,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        clean_session=True,
    )

    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    client.enable_logger()

    client.on_connect = on_mqtt_connect
    client.on_disconnect = on_mqtt_disconnect

    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_start()

    mqtt_client = client

    return client


def on_mqtt_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        log.info("Connected to MQTT broker")

        publish_discovery(client)

    else:
        log.error(f"MQTT connect failed: {reason_code}")


def on_mqtt_disconnect(client, userdata, flags, reason_code, properties):
    log.warning(f"MQTT disconnected: {reason_code}")


# ==================================================
# Home Assistant Discovery
# ==================================================

def publish_discovery(client):

    payload = {
        "name": DEVICE_NAME,
        "state_topic": STATE_TOPIC,
        "unique_id": DEVICE_ID,
        "icon": "mdi:nfc",

        "device": {
            "identifiers": [DEVICE_ID],
            "name": DEVICE_NAME,
            "model": "USB NFC Reader",
            "manufacturer": "DIY",
        },
    }

    client.publish(
        DISCOVERY_TOPIC,
        json.dumps(payload),
        retain=True
    )

    log.info("Published Home Assistant discovery config")


# ==================================================
# NFC Handling
# ==================================================

class NFCObserver(CardObserver):

    def __init__(self, mqtt_client):
        self.client = mqtt_client
        self.last_uid = None

    def update(self, observable, actions):

        (added_cards, removed_cards) = actions

        for card in added_cards:
            self.handle_card(card)

        for card in removed_cards:
            self.last_uid = None


    def handle_card(self, card):

        try:
            connection = card.createConnection()
            connection.connect()

            # Get UID
            apdu = [0xFF, 0xCA, 0x00, 0x00, 0x00]
            data, sw1, sw2 = connection.transmit(apdu)

            if sw1 != 0x90:
                return

            uid = toHexString(data)

            if uid == self.last_uid:
                return

            self.last_uid = uid

            log.info(f"Tag detected: {uid}")

            self.publish(uid)

        except NoCardException:
            pass

        except Exception as e:
            log.error(f"Card error: {e}")

    
    def publish(self, uid):
    
        # Update sensor state
        self.client.publish(
            STATE_TOPIC,
            uid,
            qos=1,
            retain=False
        )
    
        # Home Assistant Tag scan (OFFICIAL API)
        tag_payload = {
            "tag_id": uid.replace(" ", "")
        }
    
        self.client.publish(
            "homeassistant/tag/scanned",
            json.dumps(tag_payload),
            qos=1,
            retain=False
        )
    
        log.info("Published tag scan to Home Assistant")

# ==================================================
# Reader Wait
# ==================================================

def wait_for_reader():

    log.info("Waiting for NFC reader...")

    while True:

        r = readers()

        if r:
            log.info(f"Using reader: {r[0]}")
            return

        time.sleep(2)


# ==================================================
# Main
# ==================================================

def main():

    log.info("Starting NFC MQTT Bridge (event-based)")

    if not MQTT_HOST:
        log.error("MQTT_HOST not set")
        exit(1)

    setup_mqtt()

    wait_for_reader()

    monitor = CardMonitor()
    observer = NFCObserver(mqtt_client)

    monitor.addObserver(observer)

    log.info("NFC reader monitoring started")

    # Keep main thread alive
    try:
        while True:
            time.sleep(60)

    except KeyboardInterrupt:
        log.info("Shutting down")


if __name__ == "__main__":
    main()
