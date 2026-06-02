"""
Nirvana OS - USB Serial Reader for ESP32
Reads sensor data from ESP32 over USB cable and saves it to data.csv
Using Time-Lapse 5-Minute Epoch increments.
"""
import serial
import serial.tools.list_ports
import csv
import os
import sys
import time
from datetime import datetime, timedelta

CSV_FILE = os.path.join(os.path.dirname(__file__), "data.csv")

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

def get_next_timestamp():
    """Reads data.csv and calculates the next logical 5-minute epoch timestamp."""
    if os.path.exists(CSV_FILE) and os.path.getsize(CSV_FILE) > 0:
        try:
            with open(CSV_FILE, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
                if len(rows) > 1:
                    last_time_str = rows[-1][0].strip()
                    try:
                        last_time = datetime.strptime(last_time_str, "%H:%M")
                        next_time = last_time + timedelta(minutes=5)
                        return next_time.strftime("%H:%M")
                    except ValueError:
                        pass
        except Exception as e:
            print(f"[WARN] Error reading last timestamp: {e}")
            
    return "22:00"

def main():
    if len(sys.argv) > 1:
        port = sys.argv[1]
    else:
        port = find_esp32_port()
    
    if not port:
        print("[ERROR] No COM ports found. Is your ESP32 plugged in via USB?")
        sys.exit(1)
    
    # Ensure CSV file has headers
    if not os.path.exists(CSV_FILE) or os.path.getsize(CSV_FILE) == 0:
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "heart_rate", "movement", "light", "stress"])
        print("[NIRVANA] Initialized fresh data.csv")
    
    print(f"\n{'='*50}")
    print(f"  NIRVANA USB SERIAL READER (5-MIN TIME-LAPSE MODE)")
    print(f"  Listening on: {port} @ 9600 baud")
    print(f"  Each ESP32 signal increments simulation clock by 5 mins.")
    print(f"  Press Ctrl+C to stop")
    print(f"{'='*50}\n")
    
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
                    
                    # Calculate stress
                    stress = (hr * 0.26) + (mv * 4.6) + (lt * 0.015)
                    
                    # Get next 5-minute epoch timestamp
                    timestamp = get_next_timestamp()
                    
                    # Save to CSV
                    with open(CSV_FILE, "a", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow([timestamp, hr, mv, lt, f"{stress:.2f}"])
                    
                    print(f"[{timestamp}] HR: {hr} | MV: {mv} | LT: {lt} | STRESS: {stress:.2f}")
                    
                except ValueError:
                    print(f"[WARN] Skipping malformed data: {line}")
            else:
                print(f"[INFO] ESP32: {line}")
                
    except serial.SerialException as e:
        print(f"[ERROR] Could not open {port}: {e}")
        print("[TIP] Make sure the Arduino Serial Monitor is CLOSED before running this script.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[STOP] Serial reader stopped safely.")
        ser.close()

if __name__ == "__main__":
    main()
