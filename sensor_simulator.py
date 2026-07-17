"""
Nirvana OS - Advanced Biometric Telemetry Simulator
Simulates sensor data and posts it to Flask API telemetry endpoint.
"""
import random
import time
import requests
from datetime import datetime

API_URL = "http://127.0.0.1:5000/api/telemetry"

print("====================================================")
print("   Nirvana HIGH-FIDELITY BIOMETRIC SIMULATION ENGINE ")
print("   Posting telemetry data to: " + API_URL)
print("====================================================")

try:
    while True:
        timestamp_str = datetime.now().strftime("%H:%M:%S")
        
        # Simulate realistic nocturnal biological trends
        heart_rate = random.randint(58, 112)
        movement_frequency = random.randint(0, 10)
        ambient_lux = random.randint(0, 750)

        # Baseline logic equation used to train the machine learning system
        calculated_stress = (heart_rate * 0.26) + (movement_frequency * 4.6) + (ambient_lux * 0.015)
        clean_stress_metric = "{:.2f}".format(calculated_stress)
        
        # Post data to Flask app telemetry API
        payload = {
            "heart_rate": heart_rate,
            "movement": movement_frequency,
            "light": ambient_lux
        }
        
        try:
            response = requests.post(API_URL, json=payload, timeout=2)
            if response.status_code == 200:
                print(f"[{timestamp_str}] Posted -> CARDIO: {heart_rate} BPM | MOTION: {movement_frequency} Hz | LIGHT: {ambient_lux} Lux (Status: {response.status_code})")
            else:
                print(f"[{timestamp_str}] [WARN] Server returned error {response.status_code}: {response.text}")
        except requests.RequestException as e:
            print(f"[{timestamp_str}] [ERROR] Failed to post telemetry to Flask API: {e}")
            print("          Is the Flask app running on port 5000?")
        
        time.sleep(2)
        
except KeyboardInterrupt:
    print("\n[STOP] Telemetry generation interrupted safely.")