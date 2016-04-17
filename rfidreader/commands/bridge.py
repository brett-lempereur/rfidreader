"""
This command provides a bridge between the RFID reader and an MQTT
broker, emitting messages when a card is presented and removed.
"""

import argparse
import time

import paho.mqtt.client

import rfidreader.hardware

# Message broker topics.
PRESENTED_TOPIC = "rfid/presented"
REMOVED_TOPIC = "rfid/removed"

# Build the command-line argument parser.
parser = argparse.ArgumentParser(description="RFID to MQTT bridge")
parser.add_argument("hostname", help="Message broker hostname")
parser.add_argument("port", type=int, help="Message broker port")

def loop(rfid, client, delay=0.1):
    """
    Main loop that reads from an RFID reader and emits presence and
    removal events over an MQTT broker.

    :param rfid: the rfid reader instance.
    :param client: message broker client.
    :param delay: delay between iterations.
    """
    present = None
    while True:
        response = rfid.select()
        if response is not None:
            if present != response:
                present = response
                client.publish(PRESENTED_TOPIC, response[1])
        else:
            if present is not None:
                present = None
                client.publish(REMOVED_TOPIC)
        time.sleep(delay)

def main():
    """
    Main entry point.
    """
    # Parse command-line arguments.
    args = parser.parse_args()
    # Connect to the MQTT broker.
    client = paho.mqtt.client.Client()
    client.connect(args.host, args.port)
    client.loop_start()
    try:
        # Create the RFID reader instance.
        rfid = rfidreader.hardware.RFIDReader(1, 0x50, 4, None)
        # Start the main loop.
        loop(rfid, client)
    finally:
        client.loop_stop()
