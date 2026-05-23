# Nirvana | Technical Implementation Plan & Somatic Routing Spec

This document outlines the architectural specifications, system layout, routing changes, and stress indices designed and implemented for the **Nirvana** Platform (Real-Time Somatic Analysis & Academic Stress Monitoring).

---

## Architectural Layout & Telemetry Routes

Nirvana's server infrastructure divides user access between marketing, technical explanations, and a real-time clinical monitoring suite:

1. **`templates/index.html` (Landing Page)**
   - Serves as the core entry page at the root URL `/`.
   - Built on a pristine, high-end white background with custom ice-cyan styling tokens.
   - Houses the cinematic staggered vertical pop-up letter animation for the central title **NIRVANA**.
   - Interfaces with the Flask `/data` endpoint to poll current metrics directly, showing a live preview of telemetry state variables.
   - Redirects visitors to `/dashboard` for active session tracking.

2. **`templates/dashboard.html` (Live Telemetry Dashboard)**
   - Relocated from original index page and exposed via route `/dashboard`.
   - Offers an advanced dark-themed workspace (`#080c14` to `#0c1424`) with glassmorphic cards and soft drop shadows.
   - Hosts real-time Chart.js telemetry waveforms (MAX30102 Cardio, MPU6050 Actigraphy, LDR Ambient Lux).
   - Displays concentric circular rings mapping physiological sleep phases and dynamic diagnostic lists.

3. **Backend API Endpoints (`app.py`)**
   - `@app.route("/")`: Renders `index.html`.
   - `@app.route("/dashboard")`: Renders `dashboard.html`.
   - `@app.route("/data")`: Returns the last recorded somatic telemetry frame in JSON format.
   - `@app.route("/predict")`: Calculates the current stress index using a pre-trained regression model (`model.py`).

---

## 5-Tier Somatic Stress Response Scale

Nirvana integrates a scientific, multi-dimensional somatic classification scale to map heart rate (BPM), motion kinematics (Hz), and photic ambient exposure (Lux) to academic strain:

* **Tier 1 (0–20): Deep Recovery / Restorative State**
  - *Somatic Indicators:* Low movement threshold, parasympathetic dominance, low heart rate (e.g., 50–65 BPM).
  - *Context:* Typical of deep slow-wave sleep (N3), facilitating neural clearance and memory consolidation.

* **Tier 2 (21–40): Calm Waking / Focused Alertness**
  - *Somatic Indicators:* Minimal kinetics (< 2Hz), stable resting heart rate (66–75 BPM), low lux exposure.
  - *Context:* High cognitive focus, ideal state for programming, reading, and systematic problem-solving.

* **Tier 3 (41–60): Active Waking / Alert Engagement**
  - *Somatic Indicators:* Moderate movement vectors, normal active heart rate (76–85 BPM).
  - *Context:* Productive day-to-day engagement, collaborative discussions, and typical daytime cognitive loads.

* **Tier 4 (61–80): Sympathetic Activation / Somatic Strain**
  - *Somatic Indicators:* Spiked kinetic metrics, elevated nocturnal cardio (> 85 BPM), light disturbance.
  - *Context:* Academic fatigue, acute anxiety indicators, or early stages of physical/mental stress response.

* **Tier 5 (81–100): Extreme Stress / Somatic Overload**
  - *Somatic Indicators:* Tachycardic pulse waveforms (> 98 BPM), high actigraphy, photic spectral blue-light threats.
  - *Context:* High-intensity mental blockages, sleep onset delays, or severe circadian rhythm disruption.

---

## Zero-Emoji Policy and UI Guidelines

To maintain an elite, clinical-grade visual presentation suitable for an academic and bio-telemetry application, a strict **Zero-Emoji Policy** is enforced:
- **No Decorative Emojis**: All standard emojis (such as `❌`, `⚠️`, `📊`, `❤️`, `⚡`) have been completely purged from both the frontend interfaces and backend Flask logs.
- **Vector Alternative**: All warnings, highlights, indicators, and buttons utilize crisp, modern vector icons imported from **FontAwesome 6.4.0** or styled SVGs.
- **Backbone Color Palette**:
  - `#E0F7FA` (Ultra-light Ice Cyan)
  - `#B2EBF2` (Pastel Light Cyan)
  - `#80DEEA` (Medium Cyan Accent)
  - `#4DD0E1` (Vibrant Tech Cyan)
  - `#26C6DA` (Deep Sky Cyan)
