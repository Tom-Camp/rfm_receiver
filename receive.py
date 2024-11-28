import json
import os
import sys
import time
from datetime import datetime

import adafruit_rfm9x
import board
import busio
import digitalio
import requests
from dotenv import load_dotenv
from loguru import logger

load_dotenv()
logger.remove()

logger.add(
    "/var/log/rfm_receiver_errors.log",
    level="ERROR",
    rotation="500 MB",
    retention="30 days",
)

logger.add(
    "/var/log/rfm_receiver_info.log",
    level="INFO",
    rotation="500 MB",
    retention="30 days",
)

logger.add(sys.stderr, level="INFO")


class LoraReceiver:
    def __init__(self, frequency: int = 915):
        """
        Initialize LoRa receiver

        :param frequency: Frequency in MHz
        """

        cs = digitalio.DigitalInOut(board.CE1)
        reset = digitalio.DigitalInOut(board.D25)
        spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

        self.rfm9x = adafruit_rfm9x.RFM9x(spi, cs, reset, frequency)
        self.rfm9x.tx_power = 23
        self.rfm9x.spreading_factor = 7
        self.rfm9x.signal_bandwidth = 125000
        self.rfm9x.coding_rate = 5
        self.rfm9x.enable_crc = True
        self.rfm9x.receive_timeout = 5.0

    def receive_data(self) -> tuple:
        try:
            packet = self.rfm9x.receive()
            if packet is not None:
                try:
                    packet_text = packet.decode()
                except UnicodeDecodeError:
                    packet_text = packet
                packet_data = json.loads(packet_text)

                sid = packet_data.get("sender_id", "UNKNOWN")
                sensor_data = packet_data.get("data", {})
                received_at = datetime.now().strftime("%Y-%m-%d %H:%M")

                if sid and sensor_data:
                    sensor_data["time"] = received_at
                    self._post_data(sid=sid, sensor_data=sensor_data)
                    return sid, sensor_data

            return None, None

        except IOError as er:
            logger.error(f"Error receiving data: {er}")
            return None, None

    @staticmethod
    def _post_data(sid: str, sensor_data: dict):
        url = str(os.getenv("PURL"))
        post_data: dict = {
            "key": sid,
            "data": sensor_data,
        }
        token = os.getenv("PTOKEN")
        headers: dict = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        try:
            response = requests.post(url, json=post_data, headers=headers)
            response.raise_for_status()

            logger.info(f"Status Code: {response.status_code}")
            logger.info(f"Response JSON: {response.json()}")
        except requests.exceptions.RequestException as e:
            logger.error(f"An error occurred: {e}")


if __name__ == "__main__":
    receiver = LoraReceiver()
    logger.info("LoRa Receiver initialized. Waiting for messages...")

    while True:
        try:
            sender_id, data = receiver.receive_data()

            if sender_id is not None:
                logger.info(f"Received from {sender_id}:")
                logger.info(f"Received message: {data}")

            time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(1)
