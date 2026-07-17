# Nirvana ESP32 Firmware & Hardware Integration

This directory contains the firmware and hardware instructions for connecting the ESP32 microcontroller to the Nirvana Intelligence Platform.

## Directory Structure

- `esp32_firmware/esp32_firmware.ino`: Arduino/C++ sketch to flash to the ESP32 board.

## Hardware Connections

Connect the sensors to the ESP32 as follows (default pins used in the sketch):

| Sensor | Sensor Output Pin | ESP32 GPIO Pin |
|---|---|---|
| **Pulse Sensor (Heart Rate)** | Analog Out | GPIO 34 (Analog input pin) |
| **LDR (Ambient Light Sensor)** | Analog Out | GPIO 35 (Analog input pin) |
| **Accelerometer / Motion** | Analog/Digital | Currently simulated via random ranges (expand to I2C/analog) |

## Flashing Instructions

1. Install the Arduino IDE or PlatformIO.
2. Open the Arduino IDE and load `esp32_firmware/esp32_firmware.ino`.
3. Select your ESP32 Dev Module board model (under **Tools > Board**).
4. Connect your ESP32 to your PC using a micro-USB or USB-C cable.
5. Choose the correct COM Port (under **Tools > Port**).
6. Click **Upload**.

## Serial Handshake Protocol

When the ESP32 restarts, it outputs:
```
NIRVANA_ESP32_READY
```
This signals to the `serial_reader.py` script that the connection is active and hardware is online.

Every 3 seconds, the ESP32 transmits a CSV data packet in the following format:
```
heart_rate,movement,light
```
*Example: `85,2,45`*
