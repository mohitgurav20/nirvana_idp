import os
from dotenv import load_dotenv

# Load environment variables from .env relative to app.py
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

print("Initializing Nirvana Intelligence Platform Engine...")

from flask import Flask, jsonify, render_template, request
import pandas as pd
import joblib
import csv
from datetime import datetime, timedelta
import threading
import time
import random
import google.generativeai as genai

app = Flask(__name__)
CSV_FILE = os.path.join(os.path.dirname(__file__), "data.csv")
MODEL_FILE = os.path.join(os.path.dirname(__file__), "model.pkl")

# --- Gemini API Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-2.5-flash')
else:
    print("[WARNING] GEMINI_API_KEY not found in .env. Copilot will run in Mock Mode.")
    gemini_model = None

# --- ML Model Loading ---
if os.path.exists(MODEL_FILE):
    model_instance = joblib.load(MODEL_FILE)
    print(f"[SUCCESS] Pre-trained Machine Learning model loaded from {MODEL_FILE}")
else:
    print(f"[WARNING] {MODEL_FILE} not found. Please run model.py to train the system.")
    model_instance = None


def load_and_clean_data():
    try:
        if os.path.exists(CSV_FILE) and os.path.getsize(CSV_FILE) > 0:
            with open(CSV_FILE, 'r') as f:
                data = pd.read_csv(f)
            data.columns = data.columns.str.strip()
            required = ["timestamp", "heart_rate", "movement", "light", "stress"]
            if all(col in data.columns for col in required):
                for col in ["heart_rate", "movement", "light", "stress"]:
                    data[col] = pd.to_numeric(data[col], errors='coerce')
                return data.dropna()
        return pd.DataFrame(columns=["timestamp", "heart_rate", "movement", "light", "stress"])
    except Exception as e:
        print(f"CRITICAL: Telemetry parsing anomaly: {e}")
        return pd.DataFrame(columns=["timestamp", "heart_rate", "movement", "light", "stress"])


def seed_data_file():
    """Seed data.csv with 6 hours of historical sleep data in 5-minute increments if empty."""
    # Force delete existing csv if it contains non-5-minute formatted entries or is empty/corrupt
    needs_seeding = True
    if os.path.exists(CSV_FILE) and os.path.getsize(CSV_FILE) > 0:
        try:
            df = pd.read_csv(CSV_FILE)
            if len(df) >= 20 and ":" in str(df.iloc[0]["timestamp"]) and len(str(df.iloc[0]["timestamp"]).split(":")) == 2:
                # Correct format (HH:MM) exists and has enough rows, no need to overwrite
                needs_seeding = False
                print(f"[NIRVANA] data.csv already contains {len(df)} 5-minute epoch records. Skipping seeding.")
        except Exception:
            pass

    if needs_seeding:
        print("[NIRVANA] Seeding data.csv with 6 hours of historical sleep data (5-minute epochs)...")
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "heart_rate", "movement", "light", "stress"])
            
            # Start at 22:00 (10 PM)
            current_time = datetime.strptime("22:00", "%H:%M")
            
            # Seed 72 intervals of 5 minutes (6 hours -> 22:00 to 04:00)
            for i in range(72):
                # Calculate cyclic patterns for 3 sleep cycles (2 hours / 24 intervals per cycle)
                cycle_progress = (i % 24) / 24.0
                
                if cycle_progress < 0.15:      # Awake / Falling asleep
                    hr = random.randint(78, 88)
                    mv = random.randint(4, 7)
                    lt = random.randint(20, 50)
                elif cycle_progress < 0.45:    # Light sleep (N1/N2)
                    hr = random.randint(64, 74)
                    mv = random.randint(1, 3)
                    lt = 0
                elif cycle_progress < 0.75:    # Deep sleep (N3)
                    hr = random.randint(55, 62)
                    mv = 0
                    lt = 0
                else:                          # REM sleep
                    hr = random.randint(63, 70)
                    mv = random.randint(1, 2)
                    lt = 0
                    
                if model_instance:
                    stress = model_instance.predict([[hr, mv, lt]])[0]
                else:
                    stress = (hr * 0.26) + (mv * 4.6) + (lt * 0.015)
                    
                timestamp_str = current_time.strftime("%H:%M")
                writer.writerow([timestamp_str, hr, mv, lt, f"{stress:.2f}"])
                
                current_time += timedelta(minutes=5)


# --- ESP32 Hardware Ingestion Route ---
@app.route("/api/telemetry", methods=["POST"])
def ingest_esp32_data():
    try:
        payload = request.json
        if not payload:
            return jsonify({"error": "Invalid JSON"}), 400
        
        heart_rate = float(payload.get("heart_rate", 60))
        movement = float(payload.get("movement", 0))
        light = float(payload.get("light", 0))
        
        # Calculate stress
        if model_instance:
            predicted_stress = model_instance.predict([[heart_rate, movement, light]])[0]
        else:
            predicted_stress = (heart_rate * 0.26) + (movement * 4.6) + (light * 0.015)
            
        clean_stress = "{:.2f}".format(predicted_stress)
        
        # Calculate next 5-minute epoch timestamp
        data = load_and_clean_data()
        if not data.empty:
            last_time_str = str(data.iloc[-1]["timestamp"])
            try:
                last_time = datetime.strptime(last_time_str, "%H:%M")
            except ValueError:
                last_time = datetime.strptime("04:00", "%H:%M")
        else:
            last_time = datetime.strptime("22:00", "%H:%M")
            
        next_time = last_time + timedelta(minutes=5)
        next_time_str = next_time.strftime("%H:%M")
        
        # Save to CSV
        with open(CSV_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([next_time_str, heart_rate, movement, light, clean_stress])
            
        return jsonify({"status": "success", "message": "Telemetry securely saved."}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- Background Simulator (Fallback/Presentation Mode) ---
SIMULATION_MODE = True # Set to False once ESP32 is fully wired & writing via serial_reader.py
def background_simulator():
    # Make sure database is seeded first
    seed_data_file()
    
    while SIMULATION_MODE:
        data = load_and_clean_data()
        if not data.empty:
            last_time_str = str(data.iloc[-1]["timestamp"])
            try:
                last_time = datetime.strptime(last_time_str, "%H:%M")
            except ValueError:
                last_time = datetime.strptime("04:00", "%H:%M")
        else:
            last_time = datetime.strptime("22:00", "%H:%M")
            
        next_time = last_time + timedelta(minutes=5)
        next_time_str = next_time.strftime("%H:%M")
        
        total_rows = len(data)
        cycle_progress = (total_rows % 24) / 24.0
        
        if cycle_progress < 0.15:
            hr = random.randint(78, 88)
            mv = random.randint(4, 7)
            lt = random.randint(20, 50)
        elif cycle_progress < 0.45:
            hr = random.randint(64, 74)
            mv = random.randint(1, 3)
            lt = 0
        elif cycle_progress < 0.75:
            hr = random.randint(55, 62)
            mv = 0
            lt = 0
        else:
            hr = random.randint(63, 70)
            mv = random.randint(1, 2)
            lt = 0
            
        if model_instance:
            calc_stress = model_instance.predict([[hr, mv, lt]])[0]
        else:
            calc_stress = (hr * 0.26) + (mv * 4.6) + (lt * 0.015)
            
        with open(CSV_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([next_time_str, hr, mv, lt, "{:.2f}".format(calc_stress)])
        time.sleep(3)

# Start Simulator Daemon
sim_thread = threading.Thread(target=background_simulator, daemon=True)
sim_thread.start()


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/data")
def get_telemetry_stream():
    data = load_and_clean_data()
    if data.empty:
        return jsonify([])
    # Let visualizer render the entire historical sleep architecture (up to last 150 points)
    return jsonify(data.tail(150).to_dict(orient="records"))

@app.route("/predict")
def run_predictive_pipeline():
    data = load_and_clean_data()
    if data.empty or model_instance is None:
        return jsonify({"error": "Awaiting clean biometric synchronization streams..."}), 400

    try:
        last_frame = data.tail(1)
        hr = float(last_frame["heart_rate"].values[0])
        mv = float(last_frame["movement"].values[0])
        lt = float(last_frame["light"].values[0])
        
        predicted_stress = model_instance.predict([[hr, mv, lt]])[0]
        sleep_score = max(5, min(100, 100 - (predicted_stress * 0.85)))

        if mv <= 1 and hr <= 62:
            stage = "Deep Sleep N3"
        elif mv <= 3 and hr <= 74:
            stage = "REM Phase"
        elif mv <= 5 and hr <= 88:
            stage = "Light Sleep N1/N2"
        else:
            stage = "Active Wakefulness"

        alerts = []
        insights = []
        if hr > 98: alerts.append("[ALERT] Elevated nocturnal tachycardia vectors detected.")
        if mv > 8: alerts.append("[ALERT] Somatosensory disruption: High movement frequency.")
        if lt > 150: alerts.append("[ALERT] Circadian photoreceptor threat due to high lux levels.")

        if mv >= 6: insights.append("Somatic spikes observed between localized intervals.")
        if lt > 30 and hr > 80: insights.append("Stress index rising under ambient luminescence conditions.")
        if not insights: insights.append("All metabolic and neural systems within regular homeostatic baselines.")

        return jsonify({
            "stress_score": round(float(predicted_stress), 2),
            "sleep_score": round(float(sleep_score), 2),
            "sleep_stage": stage,
            "alerts": alerts,
            "insights": insights,
            "last_updated": last_frame["timestamp"].values[0] # Return the virtual clock timestamp
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/chat", methods=["POST"])
def context_aware_assistant():
    payload = request.json or {}
    user_query = payload.get("message", "")
    
    data = load_and_clean_data()
    context_str = "No recent telemetry data available."
    if not data.empty:
        last_frame = data.tail(1)
        hr = last_frame["heart_rate"].values[0]
        mv = last_frame["movement"].values[0]
        lt = last_frame["light"].values[0]
        st = last_frame["stress"].values[0]
        time_str = last_frame["timestamp"].values[0]
        context_str = f"Current Vitals (at virtual time {time_str}) -> Heart Rate: {hr} BPM, Movement: {mv}/10, Ambient Light: {lt} Lux, Stress Index: {st}."

    if gemini_model:
        prompt = f"""
        You are 'Nirvana AI', a highly advanced, medical-grade sleep and wellness copilot.
        Respond to the user's query intelligently, concisely, and professionally.
        Incorporate their live telemetry data into your analysis if relevant.
        
        User's Live Telemetry: {context_str}
        
        User Query: {user_query}
        """
        try:
            response = gemini_model.generate_content(prompt)
            reply = response.text.replace("\n", "<br>")
        except Exception as e:
            reply = f"Nirvana AI: [System Error communicating with Neural Core] {str(e)}"
    else:
        user_query_lower = user_query.lower()
        if "heart" in user_query_lower or "bpm" in user_query_lower:
            reply = "Nirvana AI: Autonomic nervous system monitoring reveals your heart rate variance is deeply linked with stage N3 deep sleep stability."
        elif "stress" in user_query_lower:
            reply = "Nirvana AI: The embedded multivariate linear regression engine estimates stress indicators by processing real-time links between actigraphy metrics, autonomic pacing, and light parameters."
        else:
            reply = f"Nirvana AI (Mock Mode): Telemetry pathways operational. {context_str} Please add a Gemini API key for true intelligence."
            
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True, port=5000)