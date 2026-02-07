import os
import time
import logging
import paho.mqtt.client as mqtt

from smartcard.System import readers
from smartcard.util import toHexString

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

    return client

def wait_for_reader():
    while True:
        r = readers()
        if r:
            log.info(f"Found reader: {r[0]}")
            return r[0]
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

            # APDU: Get UID
            apdu = [0xFF, 0xCA, 0x00, 0x00, 0x00]
            data, sw1, sw2 = connection.transmit(apdu)

            if sw1 == 0x90:
                uid = toHexString(data)

                if uid != last_uid:
                    log.info(f"Tag detected: {uid}")

                    mqtt_client.publish(
                        MQTT_TOPIC,
                        uid,
                        qos=1,
                        retain=False,
                    )

                    last_uid = uid

            time.sleep(1)

        except Exception as e:
            log.error(f"Reader error: {e}")
            last_uid = None
            time.sleep(2)

if __name__ == "__main__":
    main()
