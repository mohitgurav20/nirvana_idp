"""
NIRVAN OS - Next-Gen AI Healthcare Monitoring Platform
Backend Engine & Telemetry Routing Module
"""
print("Initializing NIRVAN Intelligence Platform Engine...")

from flask import Flask, jsonify, render_template, request
import pandas as pd
from sklearn.linear_model import LinearRegression
import os
import random
from datetime import datetime

app = Flask(__name__)
CSV_FILE = r"C:\Users\Admin\OneDrive\Desktop\SLEEPTRACKERPROJECT\data.csv"

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

def train_production_model():
    data = load_and_clean_data()
    if data.empty or len(data) < 2:
        return None
    try:
        X = data[["heart_rate", "movement", "light"]]
        y = data["stress"]
        model = LinearRegression()
        model.fit(X, y)
        return model
    except:
        return None

model_instance = None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data")
def get_telemetry_stream():
    data = load_and_clean_data()
    if data.empty:
        return jsonify([])
    # Return last 30 chronologically tracked rows for dynamic chart hydration
    return jsonify(data.tail(30).to_dict(orient="records"))

@app.route("/predict")
def run_predictive_pipeline():
    global model_instance
    data = load_and_clean_data()
    if model_instance is None:
        model_instance = train_production_model()
        
    if data.empty or model_instance is None:
        return jsonify({"error": "Awaiting clean biometric synchronization streams..."}), 400

    try:
        last_frame = data.tail(1)
        hr = float(last_frame["heart_rate"].values[0])
        mv = float(last_frame["movement"].values[0])
        lt = float(last_frame["light"].values[0])
        
        predicted_stress = model_instance.predict([[hr, mv, lt]])[0]
        # Calculate premium sleep index baseline metrics inversion
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
        if hr > 98: alerts.append("⚠️ Elevated nocturnal tachycardia vectors detected.")
        if mv > 8: alerts.append("⚠️ Somatosensory disruption: High movement frequency.")
        if lt > 350: alerts.append("⚠️ Circadian photoreceptor threat due to high lux levels.")

        if mv >= 6: insights.append("Somatic spikes observed between localized intervals.")
        if lt > 150 and hr > 80: insights.append("Stress index rising under unoptimized ambient luminescence conditions.")
        if not insights: insights.append("All metabolic and neural systems within regular homeostatic baselines.")

        return jsonify({
            "stress_score": round(float(predicted_stress), 2),
            "sleep_score": round(float(sleep_score), 2),
            "sleep_stage": stage,
            "alerts": alerts,
            "insights": insights,
            "last_updated": datetime.now().strftime("%H:%M:%S")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/chat", methods=["POST"])
def context_aware_assistant():
    payload = request.json or {}
    user_query = payload.get("message", "").lower()
    
    # Predefined smart medical-grade structural responses
    if "heart" in user_query or "bpm" in user_query:
        reply = "NIRVAN AI: Autonomic nervous system monitoring reveals your heart rate variance is deeply linked with stage N3 deep sleep stability. Lower resting heart rates are optimal for cellular repairs."
    elif "stress" in user_query or "regression" in user_query:
        reply = "NIRVAN AI: The embedded multivariate linear regression engine estimates stress indicators by processing real-time links between actigraphy metrics, autonomic pacing, and light parameters."
    elif "movement" in user_query or "restless" in user_query:
        reply = "NIRVAN AI: Frequent movement spikes typically indicate brief micro-arousals. This points to possible adjustments in sleep position or environmental interferences."
    elif "light" in user_query or "lux" in user_query:
        reply = "NIRVAN AI: High ambient light levels can disrupt natural melatonin synthesis. Keeping light levels below 50 Lux helps safeguard your circadian rhythm."
    else:
        reply = "NIRVAN AI: Telemetry pathways are fully operational. I am tracking your biometrics in real time. Feel free to ask about your heart rate trends, sleep stage classification models, or environmental metrics."
        
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True, port=5000)