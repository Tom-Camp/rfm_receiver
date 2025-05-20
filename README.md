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

Create a Systemd service to run the receiver on boot. First create a new service file:

```shell
sudo nano /etc/systemd/system/rfm_receiver.service
```

Add the following content to the file:

```ini
[Unit]
Description=RFM9x Receiver
After=network.target

[Service]
Type=simple
User=root
Group=spi
WorkingDirectory=/[PATH TO THIS CODE]rfm_receiver
Environment=PYTHONUNBUFFERED=1
ExecStart=/[PATH TO THIS CODE]/rfm_receiver/venv/bin/python3 /[PATH TO THIS CODE]/rfm_receiver/receive.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Make sure to replace `[PATH TO THIS CODE]` with the actual path to the code on your Raspberry Pi.
Then enable and start the service:

```shell
sudo systemctl daemon-reload
sudo systemctl enable rfm_receiver.service
sudo systemctl start rfm_receiver.service
```

You can check the status of the service with:

```shell
sudo systemctl status rfm_receiver.service
```
