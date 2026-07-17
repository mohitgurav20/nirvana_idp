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
MAX_CSV_ROWS = 200  # Cap rows to prevent file bloat

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
            data = pd.read_csv(CSV_FILE)
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


def predict_stress(hr, mv, lt):
    """Predict stress using the ML model with proper DataFrame input."""
    if model_instance:
        input_df = pd.DataFrame([[hr, mv, lt]], columns=["heart_rate", "movement", "light"])
        return model_instance.predict(input_df)[0]
    else:
        return (hr * 0.26) + (mv * 4.6) + (lt * 0.015)


def trim_csv_if_needed():
    """Keep CSV file capped at MAX_CSV_ROWS to prevent bloat."""
    try:
        df = pd.read_csv(CSV_FILE)
        if len(df) > MAX_CSV_ROWS:
            df = df.tail(MAX_CSV_ROWS)
            df.to_csv(CSV_FILE, index=False)
    except Exception:
        pass


def seed_data_file():
    """Seed data.csv with recent historical data using REAL timestamps going back from now."""
    needs_seeding = True
    if os.path.exists(CSV_FILE) and os.path.getsize(CSV_FILE) > 0:
        try:
            df = pd.read_csv(CSV_FILE)
            if len(df) >= 10:
                needs_seeding = False
                print(f"[NIRVANA] data.csv already contains {len(df)} records. Skipping seeding.")
        except Exception:
            pass

    if needs_seeding:
        print("[NIRVANA] Seeding data.csv with 1 hour of real-time historical data...")
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "heart_rate", "movement", "light", "stress"])
            
            now = datetime.now()
            for i in range(12, 0, -1):
                past_time = now - timedelta(minutes=i * 5)
                cycle_progress = (i % 6) / 6.0
                
                if cycle_progress < 0.3:
                    hr = random.randint(68, 78)
                    mv = random.randint(2, 5)
                    lt = random.randint(5, 30)
                elif cycle_progress < 0.6:
                    hr = random.randint(60, 70)
                    mv = random.randint(0, 2)
                    lt = random.randint(0, 10)
                else:
                    hr = random.randint(55, 65)
                    mv = random.randint(0, 1)
                    lt = 0
                    
                stress = predict_stress(hr, mv, lt)
                    
                timestamp_str = past_time.strftime("%H:%M:%S")
                writer.writerow([timestamp_str, hr, mv, lt, f"{stress:.2f}"])


# --- ESP32 Hardware Ingestion Route ---
@app.route("/api/telemetry", methods=["POST"])
def ingest_esp32_data():
    global SIMULATION_MODE
    try:
        payload = request.json
        if not payload:
            return jsonify({"error": "Invalid JSON"}), 400
        
        # If we get real hardware data, automatically disable background simulation
        if SIMULATION_MODE:
            print("[NIRVANA] Real telemetry detected! Disabling background simulation mode.")
            SIMULATION_MODE = False
        
        heart_rate = float(payload.get("heart_rate", 60))
        movement = float(payload.get("movement", 0))
        light = float(payload.get("light", 0))
        
        # Calculate stress
        predicted_stress = predict_stress(heart_rate, movement, light)
        clean_stress = "{:.2f}".format(predicted_stress)
        
        # Use REAL current timestamp
        real_timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Save to CSV
        with open(CSV_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([real_timestamp, heart_rate, movement, light, clean_stress])
        trim_csv_if_needed()
            
        return jsonify({"status": "success", "timestamp": real_timestamp, "message": "Telemetry saved."}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- Background Simulator (Fallback/Presentation Mode) ---
# Generates realistic sensor data with REAL timestamps every 5 seconds
SIMULATION_MODE = True  # Set to False once ESP32 is connected via serial_reader.py

def background_simulator():
    # Make sure database is seeded first
    seed_data_file()
    
    while SIMULATION_MODE:
        data = load_and_clean_data()
        total_rows = len(data)
        cycle_progress = (total_rows % 24) / 24.0
        
        if cycle_progress < 0.15:
            hr = random.randint(72, 85)
            mv = random.randint(3, 6)
            lt = random.randint(10, 40)
        elif cycle_progress < 0.45:
            hr = random.randint(62, 72)
            mv = random.randint(1, 3)
            lt = random.randint(0, 5)
        elif cycle_progress < 0.75:
            hr = random.randint(55, 63)
            mv = random.randint(0, 1)
            lt = 0
        else:
            hr = random.randint(60, 68)
            mv = random.randint(1, 2)
            lt = 0
            
        calc_stress = predict_stress(hr, mv, lt)
        
        # Use REAL current timestamp
        real_timestamp = datetime.now().strftime("%H:%M:%S")
            
        with open(CSV_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([real_timestamp, hr, mv, lt, "{:.2f}".format(calc_stress)])
        trim_csv_if_needed()
        time.sleep(5)  # New data every 5 seconds

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
        
        predicted_stress = predict_stress(hr, mv, lt)
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