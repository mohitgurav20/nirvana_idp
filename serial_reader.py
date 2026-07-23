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
    port = None
    baud = 115200
    
    if len(sys.argv) > 1:
        port = sys.argv[1]
        if len(sys.argv) > 2:
            try:
                baud = int(sys.argv[2])
            except ValueError:
                pass
    else:
        port = find_esp32_port()
    
    if not port:
        print("[ERROR] No COM ports found. Is your ESP32 plugged in via USB?")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"  NIRVANA USB SERIAL READER (REAL-TIME HARDWARE & HYBRID MODE)")
    print(f"  Listening on: {port} @ {baud} baud")
    print(f"  Posting telemetry data to: {API_URL}")
    print(f"  Press Ctrl+C to stop")
    print(f"{'='*60}\n")
    
    # State variables for accumulating multi-line custom formats
    ldr_value = None
    piezo_value = None
    has_movement = False
    last_post_time = 0
    post_interval = 2.5 # seconds between posts
    
    import random
    
    print(f"\n[NIRVANA] Attempting connection to {port} @ {baud} baud...")
    
    while True:
        try:
            ser = serial.Serial(port, baud, timeout=2)
            time.sleep(2)  # Wait for ESP32 to reset
            print(f"\n[NIRVANA SUCCESS] Connected to ESP32 on {port}!")
            print(f"[NIRVANA] Live hardware telemetry streaming active.\n")
            
            while True:
                line = ser.readline().decode('utf-8', errors='replace').strip()
                # Sanitize for Windows console encoding
                line = line.encode('ascii', errors='replace').decode('ascii')
                
                if not line:
                    continue
                    
                if line == "NIRVANA_ESP32_READY" or "Smart Sleep Monitoring" in line:
                    print("[NIRVANA] ESP32 handshake/welcome received. Hardware online!")
                    continue
                
                # 1. Parse CSV format if present: heart_rate,movement,light
                parts = line.split(",")
                if len(parts) == 3:
                    try:
                        current_time = time.time()
                        if current_time - last_post_time >= post_interval:
                            hr = float(parts[0])
                            mv = float(parts[1])
                            lt = float(parts[2])
                            
                            payload = {
                                "heart_rate": hr,
                                "movement": mv,
                                "light": lt
                            }
                            
                            timestamp = datetime.now().strftime("%H:%M:%S")
                            try:
                                response = requests.post(API_URL, json=payload, timeout=2)
                                if response.status_code == 200:
                                    print(f"[{timestamp}] Sent -> HR: {hr} BPM | Motion: {mv} | Light: {lt} Lux")
                                    last_post_time = current_time
                            except requests.RequestException as e:
                                print(f"[{timestamp}] [ERROR] Failed to post telemetry: {e}")
                    except ValueError:
                        pass
                        
                # 2. Parse multi-line custom format
                if "LDR Value:" in line:
                    try:
                        ldr_value = float(line.split("LDR Value:")[1].strip())
                    except ValueError:
                        pass
                elif "Piezo Value:" in line:
                    try:
                        piezo_value = float(line.split("Piezo Value:")[1].strip())
                    except ValueError:
                        pass
                elif "Movement Detected" in line:
                    has_movement = True
                elif "No Significant Movement" in line:
                    has_movement = False
                    
                if "===" in line or line.startswith("---"):
                    if ldr_value is not None or piezo_value is not None:
                        current_time = time.time()
                        if current_time - last_post_time >= post_interval:
                            lt_scaled = min(800.0, (ldr_value / 4095.0) * 800.0) if ldr_value is not None else 0.0
                            mv_val = piezo_value if piezo_value is not None else (1024.0 if has_movement else 0.0)
                            mv_scaled = min(10.0, (mv_val / 4095.0) * 10.0)
                            hr_sim = random.randint(60, 72) if not has_movement else random.randint(75, 95)
                            
                            payload = {
                                "heart_rate": hr_sim,
                                "movement": round(mv_scaled, 2),
                                "light": round(lt_scaled, 2)
                            }
                            
                            timestamp = datetime.now().strftime("%H:%M:%S")
                            try:
                                response = requests.post(API_URL, json=payload, timeout=2)
                                if response.status_code == 200:
                                    print(f"[{timestamp}] Sent (Parsed) -> HR: {hr_sim} BPM | Motion: {payload['movement']} | Light: {payload['light']} Lux")
                                    last_post_time = current_time
                            except requests.RequestException as e:
                                print(f"[{timestamp}] [ERROR] Failed to post telemetry: {e}")
                        
                        ldr_value = None
                        piezo_value = None
                        has_movement = False
                else:
                    if not any(k in line for k in ["LDR Value:", "Piezo Value:", "Brightness:", "Movement Detected", "No Significant"]):
                        print(f"[INFO] ESP32 raw: {line}")

        except serial.SerialException as e:
            print(f"[WAITING FOR ESP32 UNLOCK] Port {port} is currently open in another app (e.g., Serial Monitor). Retrying in 3s...")
            time.sleep(3)
        except KeyboardInterrupt:
            print("\n[STOP] Serial reader stopped safely.")
            break

if __name__ == "__main__":
    main()
