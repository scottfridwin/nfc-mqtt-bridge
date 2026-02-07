import os
import time
import logging

import paho.mqtt.client as mqtt

from smartcard.System import readers
from smartcard.util import toHexString
from smartcard.Exceptions import NoReadersException, CardConnectionException


# --------------------------------------------------
# Logging
# --------------------------------------------------

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

log = logging.getLogger("nfc")


# --------------------------------------------------
# MQTT Config
# --------------------------------------------------

MQTT_HOST = os.getenv("MQTT_HOST")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "homeassistant/nfc/tag")


# --------------------------------------------------
# MQTT Setup
# --------------------------------------------------

def setup_mqtt():
    client = mqtt.Client()

    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_start()

    log.info("Connected to MQTT broker")

    return client


# --------------------------------------------------
# NFC Reader Detection
# --------------------------------------------------

def wait_for_reader():
    """Wait until at least one PC/SC reader is available"""

    while True:
        try:
            r = readers()

            if r:
                log.info("Found reader: %s", r[0])
                return r[0]

            raise NoReadersException()

        except NoReadersException:
            log.warning("No NFC readers found")

        except Exception as e:
            log.warning("Reader detection error: %s", e)

        log.info("Waiting for NFC reader...")
        time.sleep(2)


# --------------------------------------------------
# Card Reading
# --------------------------------------------------

def read_uid(connection):
    """Read UID from NFC tag"""

    # GET DATA (UID)
    apdu = [0xFF, 0xCA, 0x00, 0x00, 0x00]

    data, sw1, sw2 = connection.transmit(apdu)

    if sw1 == 0x90 and sw2 == 0x00:
        return toHexString(data)

    return None


# --------------------------------------------------
# Main Loop
# --------------------------------------------------

def main():
    log.info("Starting NFC MQTT Bridge")

    mqtt_client = setup_mqtt()

    reader = wait_for_reader()

    last_uid = None
    connection = None


    while True:
        try:
            # (Re)connect if needed
            if connection is None:
                connection = reader.createConnection()
                connection.connect()

                log.info("Connected to NFC reader")


            uid = read_uid(connection)

            if uid and uid != last_uid:
                log.info("Tag detected: %s", uid)

                mqtt_client.publish(
                    MQTT_TOPIC,
                    uid,
                    qos=1,
                    retain=False
                )

                last_uid = uid


            time.sleep(1)


        except CardConnectionException:
            log.warning("Card connection lost")
            connection = None
            last_uid = None
            time.sleep(2)


        except Exception as e:
            log.error("Reader error: %s", e, exc_info=True)

            connection = None
            last_uid = None

            time.sleep(2)


# --------------------------------------------------
# Entry Point
# --------------------------------------------------

if __name__ == "__main__":
    main()
