import pandas as pd
import matplotlib.pyplot as plt
import os

CSV_FILE = "data.csv"

if not os.path.exists(CSV_FILE) or os.path.getsize(CSV_FILE) == 0:
    print("❌ Error: 'data.csv' is empty or missing. Run your simulator script first!")
    exit()

data = pd.read_csv(CSV_FILE)

plt.figure(figsize=(10, 5))
plt.plot(data["heart_rate"], label="Heart Rate (BPM)", color="#3b82f6", linewidth=2)
plt.plot(data["movement"], label="Movement Intensity", color="#6366f1", linewidth=2)
plt.plot(data["stress"], label="Stress Index Metric", color="#ef4444", linestyle="--")

plt.title("Nirvana OS | Historical Sleep Pattern Evaluation Data", fontsize=12, fontweight='bold')
plt.xlabel("Timeline Metrics (Ticks)", fontsize=10)
plt.ylabel("Value Metrics Scaled", fontsize=10)
plt.grid(True, linestyle=":", alpha=0.5)
plt.legend()
plt.tight_layout()

print("📊 Displaying your analytical tracking graph...")
plt.show()