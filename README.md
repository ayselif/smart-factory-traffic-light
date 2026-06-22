# Smart Factory Traffic Light

A Raspberry Pi-based traffic light prototype developed for the Smart Factory Lab.

## Features

- Red, yellow, and green LED control
- Realistic traffic light timings
- KY-036 touch sensor support
- Pedestrian request handling
- OPC UA server integration
- Remote monitoring with UaExpert

## Hardware

- Raspberry Pi 4 Model B
- Red, yellow, and green LEDs
- 220 ohm resistors
- Breadboard
- KY-036 touch sensor
- RB-PROTO+ shield

## GPIO Configuration

| Component | BCM GPIO | Physical Pin |
|---|---:|---:|
| Red LED | GPIO17 | 11 |
| Yellow LED | GPIO27 | 13 |
| Green LED | GPIO22 | 15 |
| Touch sensor D0 | GPIO18 | 12 |

## Touch Sensor

- A0: Not connected
- G: GND
- +: 3.3V
- D0: GPIO18

## Run

```bash
cd ~/traffic-project
source .venv/bin/activate
GPIOZERO_PIN_FACTORY=lgpio python traffic_opcua.py
