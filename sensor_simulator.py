"""
Nirvana OS - Advanced Biometric Telemetry Simulator
"""
import random
import time
import csv
import os
from datetime import datetime

CSV_FILE = os.path.join(os.path.dirname(__file__), "data.csv")

print("====================================================")
print("   Nirvana HIGH-FIDELITY BIOMETRIC SIMULATION ENGINE ")
print("====================================================")

file_exists = os.path.isfile(CSV_FILE) and os.path.getsize(CSV_FILE) > 0

if not file_exists:
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "heart_rate", "movement", "light", "stress"])
    print("[INFO] Successfully initialized fresh data.csv logs with 5-channel headers.")

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
        
        print(f"[{timestamp_str}] CARDIO: {heart_rate} BPM | MOTION: {movement_frequency} Hz | LIGHT: {ambient_lux} Lux | STRESS: {clean_stress_metric}")

        with open(CSV_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([timestamp_str, heart_rate, movement_frequency, ambient_lux, clean_stress_metric])
        
        time.sleep(2)
        
except KeyboardInterrupt:
    print("\n[STOP] Telemetry generation interrupted safely.")