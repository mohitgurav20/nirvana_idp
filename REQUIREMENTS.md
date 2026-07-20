# Nirvana | Setup & Requirements Guide

This document outlines the software and hardware requirements needed to set up and run Nirvana on a clean clone of the repository.

---

## 1. Software Prerequisites

Before installing the dependencies, ensure you have the following installed on your target machine:
* **Python 3.8 to 3.12**: Make sure Python is added to your system's PATH.
* **Arduino IDE** (Optional, only needed if modifying or uploading the ESP32 firmware).
* **Git** (For version control and cloning the repository).

---

## 2. Python Dependencies

The core backend system relies on the packages listed in `requirements.txt`. Here is a breakdown of what each library is used for:

| Package | Minimum Version | Purpose |
| :--- | :--- | :--- |
| **Flask** | `3.0.0` | Powers the web application, routing system, and API endpoints. |
| **python-dotenv** | `1.0.0` | Loads server configuration parameters and API keys from a `.env` file. |
| **google-generativeai** | `0.8.0` | Connects the telemetry system with the Gemini AI Copilot. |
| **pandas** | `2.0.0` | Handles high-performance telemetry data manipulation, CSV management, and cleanup. |
| **scikit-learn** | `1.3.0` | Trains and runs the predictive linear regression model for stress forecasting. |
| **joblib** | `1.3.0` | Serializes (saves/loads) the trained scikit-learn model weights. |
| **pyserial** | `3.5` | Reads the real-time binary/ASCII data stream from the ESP32 over a USB connection. |
| **requests** | `2.30.0` | Used by simulator and serial scripts to POST data to the Flask REST API. |

### Step-by-Step Installation:

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd nirvana_idp
   ```

2. **Create a Virtual Environment**:
   It is recommended to run Nirvana in an isolated virtual environment to prevent dependency conflicts.
   * **Windows (PowerShell)**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   * **macOS / Linux**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install Requirements**:
   Upgrade `pip` and install all necessary packages inside the activated environment:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

---

## 3. Hardware Requirements & Drivers

If you are running the platform in **Real Hardware Mode** with an ESP32 microcontroller, you need:

1. **Hardware Components**:
   * ESP32 Development Board (e.g., ESP32-WROOM-32).
   * LDR Sensor (Light Dependent Resistor) connected to analog pin `ADC1_CH6` (GPIO 34).
   * Piezo Vibration Sensor connected to analog pin `ADC1_CH7` (GPIO 35).
   * Micro-USB or USB-C cable for serial communication and power.

2. **USB-UART Drivers**:
   Depending on the bridge chip on your ESP32 board, you may need to install one of the following drivers so your computer detects the serial port:
   * **Silicon Labs CP210x Driver**: [Download here](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers)
   * **WCH CH340/CH341 Driver**: [Download here](http://www.wch-ic.com/downloads/CH341SER_EXE.html)

3. **Flashing Firmware**:
   * Open the Arduino IDE.
   * Install the ESP32 board package (`File > Preferences > Additional Board Manager URLs` and add `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`).
   * Select your ESP32 board model and connect port under `Tools`.
   * Open `firmware/esp32_firmware/esp32_firmware.ino` and upload it to the ESP32.

---

## 4. Environment Variables Setup

Nirvana's AI Copilot utilizes the Gemini API. To enable it:

1. Copy the `.env.template` file to `.env`:
   ```bash
   # Windows (PowerShell)
   Copy-Item .env.template .env
   
   # macOS / Linux / Git Bash
   cp .env.template .env
   ```
2. Edit the `.env` file and replace the placeholder API key with your key from [Google AI Studio](https://aistudio.google.com/):
   ```env
   GEMINI_API_KEY=AIzaSy...your_actual_key_here...
   ```
   *Note: If no key is set, the server runs in a restricted Mock Mode.*

---

## 5. Launch Checklist

Once requirements are met, follow this execution sequence:

1. **Initialize weights**:
   ```bash
   python model.py
   ```
2. **Start the Flask server**:
   ```bash
   python app.py
   ```
3. **Connect and run the hardware listener** (if using ESP32):
   ```bash
   python serial_reader.py
   ```
4. **Access the Dashboard**:
   Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.
