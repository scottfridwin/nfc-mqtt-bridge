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

# Scan interval
SCAN_INTERVAL = float(os.getenv("SCAN_INTERVAL", "1"))

def setup_mqtt():
    client = mqtt.Client()
    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    while True:
        try:
            client.connect(MQTT_HOST, MQTT_PORT, 60)
            client.loop_start()
            log.info("Connected to MQTT broker")
            return client
        except Exception as e:
            log.error(f"MQTT connect failed: {e}, retrying in 5s...")
            time.sleep(5)

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
            apdu = [0xFF, 0xCA, 0x00, 0x00, 0x00]
            data, sw1, sw2 = connection.transmit(apdu)

            if sw1 == 0x90 and sw2 == 0x00:
                uid = toHexString(data)
                if uid != last_uid:
                    log.info(f"Tag detected: {uid}")
                    mqtt_client.publish(MQTT_TOPIC, uid, qos=1, retain=False)
                    last_uid = uid

            time.sleep(SCAN_INTERVAL)

        except Exception as e:
            log.error(f"Reader error: {e}, reconnecting...")
            last_uid = None
            time.sleep(2)
            reader = wait_for_reader()
            connection = reader.createConnection()

if __name__ == "__main__":
    main()
