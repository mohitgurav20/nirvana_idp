# Nirvana | Real-Time Somatic Analysis & Academic Stress Monitoring

Nirvana is an advanced, clinical-grade telemetry and predictive stress monitoring platform designed for academic high-performance. Operating over a dual-interface architecture, Nirvana connects a physical (or virtual) biometric sensor suite to an intelligent machine learning regression model to track, evaluate, and predict academic strain and circadian stability.

---

## Design System & Ice-Cyan Theme

Nirvana features a bespoke, premium visual identity tailored for surgical clarity and a highly polished user experience:

- **Minimalist Light-Themed Landing Page (templates/index.html)**: Serves as a crisp, spacious entrance built on a pure white backdrop (`#ffffff`). It features an interactive typewriter terminal and an elegant, custom staggered vertical scroll-linked pop-up wave entrance for the central title **NIRVANA**.
- **High-End Dark-Themed Live Dashboard (templates/dashboard.html)**: Delivers a deep space-black canvas (`#080c14` to `#0c1424`) with glassmorphic cards carrying soft cyan drop-shadows and ice-cyan borders.
- **Ice-Cyan Color Token Scale**:
  - `#E0F7FA` (Ultra-light Ice Cyan)
  - `#B2EBF2` (Pastel Light Cyan)
  - `#80DEEA` (Medium Cool Cyan Accent)
  - `#4DD0E1` (Vibrant Technical Cyan Core)
  - `#26C6DA` (Deep Sky Cyan Highlight)
- **Clinical Aesthetics (Zero-Emoji Policy)**: Standard decorative text emojis are completely forbidden in both frontend markup and backend logs. Icons are rendered using crisp, high-fidelity SVGs or FontAwesome vector outlines.
- **Premium Typography**: Headings are set in the sharp, technical **Space Grotesk** typeface, while body copies flow naturally in readable **Outfit** typography.

---

## Key Features

| Feature | Description |
|---|---|
| **Real-Time Biometric Dashboard** | Live 2-second polling of Heart Rate, Movement, Light, and Stress from ESP32 or simulation |
| **ML Stress Prediction** | Trained linear regression model estimates stress score from raw sensor triplet |
| **Sleep Stage Classification** | Auto-classifies Deep Sleep N3, REM, Light Sleep N1/N2, and Active Wakefulness |
| **Emergency Alert System** | Pulsing red banner auto-activates when Stress > 70 or Heart Rate > 98 BPM |
| **Crisis Support Modal** | Nearest doctor contact info, animated SVG route map, and interactive breathing coach |
| **Panic Control Breathing Coach** | Box-breathing guided animation cycles (Inhale 4s / Hold 4s / Exhale 4s / Hold 4s) |
| **Gemini AI Copilot** | Context-aware chatbot answers health queries using live telemetry as context |
| **Real Hardware Auto-Switch** | When ESP32 POSTs data, simulation mode auto-disables for 100% real data |
| **Dark/Light Theme Toggle** | Persisted via localStorage, switchable in one click |

---

## Architecture & Core Components

```mermaid
graph TD
    ESP[ESP32 Hardware: firmware/] -->|USB Serial| SR[Serial Reader: serial_reader.py]
    SS[Sensor Simulator: sensor_simulator.py] -->|Mock Data POST| APP[Flask Server: app.py]
    SR -->|Real Data POST| APP
    MODEL[Regression Model: model.py] -->|Trains & Evaluates Stress| APP
    APP -->|API: /data & /predict| UI_L[Landing Page: templates/index.html]
    APP -->|API: /data & /predict| UI_D[Telemetry Dashboard: templates/dashboard.html]
```

- **`app.py`**: The central Flask backend server orchestrating somatic API requests, serves pages, and runs real-time stress index evaluation routes.
- **`model.py`**: Trains a linear regression model based on historical heart rate (BPM), movement actigraphy (Hz), and ambient lux levels to assess sleep disturbances.
- **`serial_reader.py`**: Reads real sensor telemetry from ESP32 via USB serial port, parses it, and forwards it to the Flask server in real-time.
- **`sensor_simulator.py`**: Simulates the physical telemetry suite and streams active metrics frame-by-frame to the Flask server via HTTP POST requests.
- **`firmware/`**: Arduino source code (`esp32_firmware.ino`) and wiring diagrams for the physical ESP32 hardware device.
- **`plot_data.py`**: A convenient analytical plotting utility for offline diagnostic runs.

---

## Directory Structure

```
nirvana_idp/
├── .env.template          # API key placeholder (copy to .env and fill in)
├── .gitignore             # Git ignore rules
├── README.md              # Setup & usage docs
├── requirements.txt       # Python dependencies (Flask, pandas, scikit-learn, etc.)
├── app.py                 # Flask server (routes, background simulator, Gemini chat)
├── model.py               # ML model training script
├── sensor_simulator.py    # Software-only telemetry simulator (API poster)
├── serial_reader.py       # ESP32 USB serial reader (real hardware mode)
├── plot_data.py           # Offline diagnostic chart plotter
├── firmware/
│   ├── README.md          # Hardware wiring & flash instructions
│   └── esp32_firmware/
│       └── esp32_firmware.ino  # Arduino sketch for ESP32
└── templates/
    ├── index.html         # Landing page (light theme, scroll animations)
    └── dashboard.html     # Live telemetry dashboard (dark theme, glassmorphic)
```

---

## Getting Started

### 1. Prerequisites
Ensure you have Python 3.8+ installed along with the required libraries:
```bash
pip install -r requirements.txt
```

### 2. Set Up API Key (Optional — for AI Copilot)
Copy `.env.template` to `.env` and paste your Gemini API key:
```bash
cp .env.template .env
# Then edit .env and replace 'your_gemini_api_key_here' with your key
```
Get a free key at: https://aistudio.google.com/

### 3. Train the Predictive Model
Initialize the machine learning weights before starting:
```bash
python model.py
```

### 4. Launch the Flask Server
Run the backend web app in a terminal window:
```bash
python app.py
```

### 5. Feed Telemetry Stream (Choose One Option)

#### Option A: Software Simulation (No Hardware Needed)
The Flask server automatically starts a background simulator. No extra steps needed.
Open the dashboard and data will appear within 5 seconds.

#### Option B: Real ESP32 Hardware
1. Flash the firmware from the `firmware/esp32_firmware/` directory to your ESP32.
2. Wire up the sensors as described in `firmware/README.md`.
3. Connect the ESP32 to your PC via USB.
4. Run the serial reader script (will auto-detect the COM port):
   ```bash
   python serial_reader.py
   ```
   The Flask server will **automatically detect real hardware** and disable simulation mode.

### 6. Access Dashboard
Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser to experience the platform.

---

## Emergency System

When live data crosses critical thresholds, Nirvana activates a full **Crisis Support Matrix**:

- **Trigger Conditions**:
  - Stress Index > 35 points (simulation frequently ranges between 20-50 to make automatic triggers easily testable)
  - Heart Rate > 90 BPM
- **Emergency Demo Button**: A red `⚠ EMERGENCY DEMO` button is permanently available in the header control actions hub. Clicking it instantly triggers the emergency banner and opens the Crisis Support Matrix for demonstration purposes.
- **Crisis Modal**: Opens a support overlay with:
  - India Emergency Helplines (112, 108, iCall, and Vandrevala)
  - Nearest Hospital card (pre-configured with SPARSH Hospital Yelahanka, Bengaluru with call capability)
  - Animated SVG schematic route map showing transit path
  - Interactive Panic Control Breathing Coach (box breathing: 4s Inhale / 4s Hold / 4s Exhale / 4s Hold)
  - Crisis De-escalation Checklist
  - "Download Session Report" button to export records as PDF

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Landing page |
| `GET` | `/dashboard` | Live telemetry dashboard |
| `GET` | `/data` | Returns last 150 biometric records as JSON |
| `GET` | `/predict` | Returns stress score, sleep stage, alerts, emergency status |
| `POST` | `/api/telemetry` | Accepts ESP32 hardware data `{heart_rate, movement, light}` |
| `POST` | `/chat` | Gemini AI copilot query `{message}` |
