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
    
    try:
        ser = serial.Serial(port, baud, timeout=2)
        time.sleep(2)  # Wait for ESP32 to reset
        
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
                        response = requests.post(API_URL, json=payload, timeout=2)
                        if response.status_code == 200:
                            print(f"[{timestamp}] Sent (CSV) -> HR: {hr} BPM | MV: {mv} Hz | LT: {lt} Lux")
                            last_post_time = current_time
                        else:
                            print(f"[{timestamp}] [WARN] Server returned error {response.status_code}: {response.text}")
                except Exception as e:
                    print(f"[WARN] Skipping malformed CSV: {line} ({e})")
                continue
            
            # 2. Parse custom line-by-line structured format
            # Example lines:
            # LDR Value: 4095
            # Brightness: 100%
            # Piezo Value: 4095
            # Movement Detected! / No Significant Movement
            # ================================
            
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
                
            # If we hit a block separator, send the accumulated metrics
            if "===" in line or line.startswith("---"):
                if ldr_value is not None or piezo_value is not None:
                    current_time = time.time()
                    if current_time - last_post_time >= post_interval:
                        # Map LDR Value (0-4095) to Lux range (0-800)
                        # Often light sensors read lower resistance (higher analog value) when bright
                        # We will assume LDR Value is scaled 0 to 800
                        lt_scaled = min(800.0, (ldr_value / 4095.0) * 800.0) if ldr_value is not None else 0.0
                        
                        # Map Piezo Value (0-4095) to movement scale (0-10)
                        mv_val = piezo_value if piezo_value is not None else (1024.0 if has_movement else 0.0)
                        mv_scaled = min(10.0, (mv_val / 4095.0) * 10.0)
                        
                        # Heart rate is not provided by this custom ESP32 firmware, so simulate realistically
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
                                print(f"[{timestamp}] Sent (Parsed) -> Simulated HR: {hr_sim} BPM | Motion (Piezo): {payload['movement']} | Light (LDR): {payload['light']} Lux")
                                last_post_time = current_time
                            else:
                                print(f"[{timestamp}] [WARN] Server returned error {response.status_code}: {response.text}")
                        except requests.RequestException as e:
                            print(f"[{timestamp}] [ERROR] Failed to post telemetry to Flask API: {e}")
                    
                    # Reset accumulator state for next packet
                    ldr_value = None
                    piezo_value = None
                    has_movement = False
            else:
                # If it's a line we don't recognize, print it as raw info
                if not any(k in line for k in ["LDR Value:", "Piezo Value:", "Brightness:", "Movement Detected", "No Significant"]):
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
