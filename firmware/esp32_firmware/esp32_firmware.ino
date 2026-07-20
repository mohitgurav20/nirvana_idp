#include <Arduino.h>

// --- Nirvana ESP32 Firmware ---
// Reads real sensor data and sends mapped values over USB Serial.
// Format: heart_rate,movement,light (CSV)

// --- Sensor Pins (update based on your wiring) ---
const int heartRatePin = 34;   // Analog pin for pulse sensor (PPG / Pulse Sensor)
const int lightSensorPin = 35; // Analog pin for LDR (Light Dependent Resistor)
const int movementPin = 32;    // Analog pin for piezo vibration / accelerometer

unsigned long lastTime = 0;
unsigned long timerDelay = 3000; // Send data every 3 seconds

// Smoothing buffers for noise reduction
float hr_smooth = 68.0;
float mv_smooth = 1.0;
float lt_smooth = 10.0;

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("NIRVANA_ESP32_READY");
}

void loop() {
  if ((millis() - lastTime) > timerDelay) {

    // --- Read raw analog values (ESP32 ADC: 0-4095, 12-bit) ---
    int rawHR = analogRead(heartRatePin);
    int rawLight = analogRead(lightSensorPin);
    int rawMovement = analogRead(movementPin);

    // --- Map raw analog values to realistic physiological ranges ---
    // Heart Rate: Map 0-4095 to 50-120 BPM
    float heartRate = map(rawHR, 0, 4095, 50, 120);
    // Clamp to safe range
    heartRate = constrain(heartRate, 45, 130);

    // Movement: Map 0-4095 to 0-10 Hz scale
    float movement = (rawMovement / 4095.0) * 10.0;
    movement = constrain(movement, 0.0, 10.0);

    // Light: Map 0-4095 to 0-800 Lux
    // LDR typically reads HIGH (4095) in darkness and LOW in brightness
    // Invert if your LDR wiring follows voltage divider convention
    float lightLevel = (rawLight / 4095.0) * 800.0;
    lightLevel = constrain(lightLevel, 0.0, 800.0);

    // --- Exponential smoothing to reduce ADC noise ---
    float alpha = 0.3; // smoothing factor (0.0 = ignore new, 1.0 = no smoothing)
    hr_smooth = (alpha * heartRate) + ((1.0 - alpha) * hr_smooth);
    mv_smooth = (alpha * movement) + ((1.0 - alpha) * mv_smooth);
    lt_smooth = (alpha * lightLevel) + ((1.0 - alpha) * lt_smooth);

    // --- Send as CSV over USB Serial ---
    // Format: heart_rate,movement,light
    Serial.print((int)hr_smooth);
    Serial.print(",");
    Serial.print(mv_smooth, 2);
    Serial.print(",");
    Serial.println((int)lt_smooth);

    lastTime = millis();
  }
}
