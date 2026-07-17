"""
Nirvana OS - USB Serial Reader for ESP32
Reads sensor data from ESP32 over USB cable and posts it to Flask API telemetry endpoint.
Uses real-time timestamps.
"""
import serial
import serial.tools.list_ports
import sys
import time
import requests
from datetime import datetime

API_URL = "http://127.0.0.1:5000/api/telemetry"

def find_esp32_port():
    """Auto-detect the ESP32 COM port."""
    ports = serial.tools.list_ports.comports()
    print("\n[NIRVANA] Available COM ports:")
    for p in ports:
        print(f"  -> {p.device}: {p.description}")
    
    # Try to auto-detect ESP32 by common USB-UART chip names
    for p in ports:
        desc = p.description.lower()
        if any(chip in desc for chip in ["cp210", "ch340", "ftdi", "usb-serial", "silicon labs"]):
            print(f"\n[NIRVANA] Auto-detected ESP32 on: {p.device}")
            return p.device
    
    if ports:
        print(f"\n[NIRVANA] Could not auto-detect. Using first available port: {ports[0].device}")
        return ports[0].device
    
    return None

def main():
    if len(sys.argv) > 1:
        port = sys.argv[1]
    else:
        port = find_esp32_port()
    
    if not port:
        print("[ERROR] No COM ports found. Is your ESP32 plugged in via USB?")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"  NIRVANA USB SERIAL READER (REAL-TIME HARDWARE MODE)")
    print(f"  Listening on: {port} @ 9600 baud")
    print(f"  Posting telemetry data to: {API_URL}")
    print(f"  Press Ctrl+C to stop")
    print(f"{'='*60}\n")
    
    try:
        ser = serial.Serial(port, 9600, timeout=2)
        time.sleep(2)  # Wait for ESP32 to reset
        
        while True:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            
            if not line or line == "NIRVANA_ESP32_READY":
                if line == "NIRVANA_ESP32_READY":
                    print("[NIRVANA] ESP32 handshake received. Hardware online!")
                continue
            
            # Parse CSV line: heart_rate,movement,light
            parts = line.split(",")
            if len(parts) == 3:
                try:
                    hr = float(parts[0])
                    mv = float(parts[1])
                    lt = float(parts[2])
                    
                    # Post data to Flask app telemetry API
                    payload = {
                        "heart_rate": hr,
                        "movement": mv,
                        "light": lt
                    }
                    
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    try:
                        response = requests.post(API_URL, json=payload, timeout=2)
                        if response.status_code == 200:
                            res_json = response.json()
                            stress = res_json.get("stress", "N/A") # Wait, does app.py return stress score?
                            # Let's check app.py response:
                            # return jsonify({"status": "success", "timestamp": real_timestamp, "message": "Telemetry saved."}), 200
                            # It doesn't return stress directly, but let's check if it does. It's fine either way.
                            print(f"[{timestamp}] Sent -> HR: {hr} | MV: {mv} | LT: {lt} (Status: {response.status_code})")
                        else:
                            print(f"[{timestamp}] [WARN] Server returned error {response.status_code}: {response.text}")
                    except requests.RequestException as e:
                        print(f"[{timestamp}] [ERROR] Failed to post telemetry to Flask API: {e}")
                        print("          Is the Flask app running on port 5000?")
                    
                except ValueError:
                    print(f"[WARN] Skipping malformed data: {line}")
            else:
                print(f"[INFO] ESP32 raw: {line}")
                
    except serial.SerialException as e:
        print(f"[ERROR] Could not open {port}: {e}")
        print("[TIP] Make sure the Arduino Serial Monitor is CLOSED before running this script.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[STOP] Serial reader stopped safely.")
        if 'ser' in locals() and ser.is_open:
            ser.close()

if __name__ == "__main__":
    main()
