import pandas as pd
from sklearn.linear_model import LinearRegression
import os

CSV_FILE = "data.csv"

# 1. Safety Check: Ensure data file exists and isn't empty
if not os.path.exists(CSV_FILE) or os.path.getsize(CSV_FILE) == 0:
    print("[ERROR] 'data.csv' is missing or empty. Please run 'sensor_simulator.py' first!")
    exit()

# 2. Load Data
data = pd.read_csv(CSV_FILE)

# Clean up any blank lines or missing values (NaN)
data = data.dropna()

# 3. Validation Check: Make sure we have enough data points to train a line
if len(data) < 2:
    print("[WARNING] Not enough rows in data.csv to train a model. Need at least 2 entries.")
    exit()

# 4. Define Features and Target
X = data[["heart_rate", "movement", "light"]]
y = data["stress"]

try:
    # 5. Initialize and Train Model
    model = LinearRegression()
    model.fit(X, y)
    print("[SUCCESS] Linear Regression Model trained successfully on your dataset!")

    # 6. Test Prediction using the most recent simulation row
    test = X.tail(1)
    prediction = model.predict(test)

    print("\n--- Real-time Test Run ---")
    print(f"Current Input Heart Rate: {test['heart_rate'].values[0]} BPM")
    print(f"Current Input Movement  : {test['movement'].values[0]}")
    print(f"Current Input Light Level: {test['light'].values[0]} Lux")
    print(f"Predicted Stress Output  : {round(prediction[0], 2)}")
    print("--------------------------")

except Exception as e:
    print(f"[ERROR] An error occurred during training or prediction: {e}")