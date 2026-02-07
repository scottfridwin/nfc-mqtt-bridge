#!/usr/bin/env python3

import os
import time
import logging
import threading

import paho.mqtt.client as mqtt

from smartcard.CardMonitoring import CardMonitor, CardObserver
from smartcard.util import toHexString
from smartcard.Exceptions import CardConnectionException


# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

log = logging.getLogger("nfc")


# -----------------------------------------------------------------------------
# MQTT Config
# -----------------------------------------------------------------------------

MQTT_HOST = os.getenv("MQTT_HOST")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "homeassistant/nfc/tag")


# -----------------------------------------------------------------------------
# MQTT Setup
# -----------------------------------------------------------------------------

def setup_mqtt():
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2
    )

    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    client.connect(MQTT_HOST, MQTT_PORT, 60)

    client.loop_start()

    log.info("Connected to MQTT broker at %s:%s", MQTT_HOST, MQTT_PORT)

    return client

# -----------------------------------------------------------------------------
# NFC Observer
# -----------------------------------------------------------------------------

class NFCObserver(CardObserver):
    """
    Receives card insert/remove events from PC/SC
    """

    def __init__(self, mqtt_client):
        super().__init__()

        self.mqtt = mqtt_client
        self.last_uid = None
        self.lock = threading.Lock()


    def update(self, observable, actions):
        """
        Called automatically on card insert/remove
        """

        (added_cards, removed_cards) = actions


        # Card inserted
        for card in added_cards:
            self.handle_card_insert(card)


        # Card removed
        for card in removed_cards:
            self.handle_card_remove(card)


    # -------------------------------------------------------------------------

    def handle_card_insert(self, card):

        with self.lock:

            try:
                connection = card.createConnection()
                connection.connect()

                # Get UID APDU
                apdu = [0xFF, 0xCA, 0x00, 0x00, 0x00]

                data, sw1, sw2 = connection.transmit(apdu)


                if sw1 != 0x90:
                    log.warning(
                        "Failed to read UID (SW=%02X%02X)",
                        sw1,
                        sw2,
                    )
                    return


                uid = toHexString(data)


                # Deduplicate
                if uid == self.last_uid:
                    return


                self.last_uid = uid


                log.info("Tag detected: %s", uid)


                self.mqtt.publish(
                    MQTT_TOPIC,
                    uid,
                    qos=1,
                    retain=False,
                )


            except CardConnectionException as e:
                log.warning("Card connection failed: %s", e)


            except Exception as e:
                log.error(
                    "Unexpected NFC error: %s",
                    e,
                    exc_info=True,
                )


    # -------------------------------------------------------------------------

    def handle_card_remove(self, card):

        with self.lock:

            log.info("Tag removed")

            self.last_uid = None


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main():

    log.info("Starting NFC MQTT Bridge (event-based)")


    # Sanity check
    if not MQTT_HOST:
        log.error("MQTT_HOST is not set")
        return


    # MQTT
    mqtt_client = setup_mqtt()


    # PC/SC Monitor
    card_monitor = CardMonitor()

    observer = NFCObserver(mqtt_client)

    card_monitor.addObserver(observer)


    log.info("NFC reader monitoring started")


    # Keep main thread alive forever
    try:
        while True:
            time.sleep(60)

    except KeyboardInterrupt:
        log.info("Shutting down")

    finally:
        card_monitor.deleteObserver(observer)
        mqtt_client.loop_stop()
        mqtt_client.disconnect()


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    main()
