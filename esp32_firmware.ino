#include <Arduino.h>

// --- Sensor Pins (update based on your wiring) ---
const int heartRatePin = 34;   // Analog pin for pulse sensor
const int lightSensorPin = 35; // Analog pin for LDR
// Movement can be read from an accelerometer via I2C or analog

unsigned long lastTime = 0;
unsigned long timerDelay = 3000; // Send data every 3 seconds

void setup() {
  Serial.begin(9600);
  delay(1000);
  Serial.println("NIRVANA_ESP32_READY");
}

void loop() {
  if ((millis() - lastTime) > timerDelay) {

    // --- Read your real sensors here ---
    // Replace these with actual sensor library calls for your hardware
    int heartRate = analogRead(heartRatePin);
    int lightLevel = analogRead(lightSensorPin);
    int movement = random(0, 10); // Replace with accelerometer reading

    // Map raw analog values to realistic ranges if needed
    // Example: heartRate = map(heartRate, 0, 4095, 50, 120);

    // Send as a simple CSV line over USB Serial
    // Format: heart_rate,movement,light
    Serial.print(heartRate);
    Serial.print(",");
    Serial.print(movement);
    Serial.print(",");
    Serial.println(lightLevel);

    lastTime = millis();
  }
}
