# RFM Receiver

An RFM9x receiver for a Raspberry Pi using an [Adafruit RFM95W LoRa Radio Transceiver Breakout](https://www.adafruit.com/product/3072).
The receiver listens for signals on 915MHz radio frequency and upon receipt, relays the message to an API server.

## Installation

You will need to connect the breakout board to your Raspberry Pi. If you haven't here is a
[handy guide from Adafruit](https://learn.adafruit.com/lora-and-lorawan-radio-for-raspberry-pi/raspberry-pi-wiring).

Clone the repo to your Pi and set up a virtual environment:

```shell
git clone git@github.com:Tom-Camp/rfm_receiver.git

cd rfm_receiver

python3 -m venv venv

pip install -r requirements.txt
```
