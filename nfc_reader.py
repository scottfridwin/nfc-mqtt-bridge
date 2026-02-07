import os
import time
import logging
import paho.mqtt.client as mqtt
from smartcard.scard import (
    SCardEstablishContext,
    SCARD_SCOPE_USER
)
from smartcard.pcsc.PCSCExceptions import EstablishContextException
from smartcard.util import toHexString
from smartcard.pcsc.PCSCReader import readers as pcsc_readers

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=LOG_LEVEL)
log = logging.getLogger("nfc")

# MQTT Config
MQTT_HOST = os.getenv("MQTT_HOST")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "homeassistant/nfc/tag")


def setup_mqtt():
    client = mqtt.Client()
    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_start()
    log.info("Connected to MQTT broker")
    return client


def wait_for_reader():
    """Wait for an NFC reader and force PC/SC v4 protocol context"""
    while True:
        try:
            # Force v4 context
            context = SCardEstablishContext(SCARD_SCOPE_USER)
            r = pcsc_readers(context)
            if r:
                log.info(f"Found reader: {r[0]}")
                return r[0]
        except EstablishContextException as e:
            log.warning(f"Failed to establish PC/SC context: {e}")

        log.info("Waiting for NFC reader...")
        time.sleep(2)


def main():
    log.info("Starting NFC MQTT Bridge")
    mqtt_client = setup_mqtt()
    reader = wait_for_reader()
    connection = reader.createConnection()
    last_uid = None

    while True:
        try:
            connection.connect()
            apdu = [0xFF, 0xCA, 0x00, 0x00, 0x00]
            data, sw1, sw2 = connection.transmit(apdu)

            if sw1 == 0x90:
                uid = toHexString(data)
                if uid != last_uid:
                    log.info(f"Tag detected: {uid}")
                    mqtt_client.publish(MQTT_TOPIC, uid, qos=1, retain=False)
                    last_uid = uid

            time.sleep(1)
        except Exception as e:
            log.error(f"Reader error: {e}")
            last_uid = None
            time.sleep(2)


if __name__ == "__main__":
    main()
