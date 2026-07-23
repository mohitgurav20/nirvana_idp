#include <Arduino.h>

// --- Nirvana ESP32 Firmware ---
// Reads real sensor data and sends mapped values over USB Serial.
// Format: heart_rate,movement,light (CSV)

// --- Sensor Pins ---
const int heartRatePin  = 34;  // Analog pin for pulse sensor (PPG)
const int lightSensorPin = 35; // Analog pin for LDR
const int movementPin   = 32;  // Analog pin for piezo vibration sensor

// --- Piezo Noise Filter Settings ---
// Minimum raw ADC value to count as real movement (filters out ADC noise & ringing)
const int PIEZO_THRESHOLD = 200;   // Out of 4095. Raise if still noisy, lower if too insensitive.
const int PIEZO_SAMPLES   = 10;    // Number of rapid samples to take — picks the peak
const int SAMPLE_DELAY_MS = 15;    // ms between rapid samples

// --- Cooldown: how long to suppress re-trigger after a real movement event (ms) ---
const unsigned long MOVEMENT_COOLDOWN_MS = 2000;

unsigned long lastTime        = 0;
unsigned long lastMovementTime = 0;   // Timestamp of last confirmed real movement
unsigned long timerDelay      = 3000; // Send CSV data every 3 seconds

// Smoothing state buffers
float hr_smooth = 68.0;
float mv_smooth = 0.0;
float lt_smooth = 10.0;

// --- Realistic HR simulation state (used when no pulse sensor is wired) ---
// Drifts slowly like a real resting heart rate (62–82 BPM)
float hr_state = 70.0;  // Starting resting HR
int   hr_tick  = 0;     // Tick counter for slow drift events

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("NIRVANA_ESP32_READY");
}

void loop() {
  if ((millis() - lastTime) > timerDelay) {

    // --- Heart Rate: organic slow-drift simulation ---
    // No physical pulse sensor on GPIO 34 — simulate a realistic resting HR
    // instead of mapping floating ADC noise which looks unrealistically erratic.
    hr_tick++;
    // Small random walk: ±0 or ±1 BPM each tick (gentle drift)
    int drift = random(-10, 11); // -10 to +10 (scaled /10 below)
    hr_state += drift * 0.1f;   // actual step: -1.0 to +1.0 BPM
    // Rare small event every ~10 ticks: simulates a deep breath or posture shift
    if (hr_tick % 10 == 0) {
      hr_state += random(-3, 4); // -3 to +3 BPM event
    }
    // Mean-revert gently toward 70 BPM so it never drifts far
    hr_state = hr_state * 0.97f + 70.0f * 0.03f;
    // Clamp to realistic resting range
    hr_state = constrain(hr_state, 62.0f, 82.0f);
    float heartRate = hr_state;

    // --- Light (LDR): single read ---
    int rawLight = analogRead(lightSensorPin);
    // Inverted: HIGH raw = high resistance = dark room → low Lux
    float lightLevel = ((4095 - rawLight) / 4095.0) * 800.0;
    lightLevel = constrain(lightLevel, 0.0, 800.0);

    // --- Piezo Movement: multi-sample peak detection with threshold + cooldown ---
    int peakRaw = 0;
    for (int i = 0; i < PIEZO_SAMPLES; i++) {
      int s = analogRead(movementPin);
      if (s > peakRaw) peakRaw = s;
      delay(SAMPLE_DELAY_MS);
    }

    float movement = 0.0;

    if (peakRaw >= PIEZO_THRESHOLD) {
      // Real movement confirmed — map peak to 0-10 scale
      movement = ((float)(peakRaw - PIEZO_THRESHOLD) / (float)(4095 - PIEZO_THRESHOLD)) * 10.0;
      movement = constrain(movement, 0.0, 10.0);
      lastMovementTime = millis();
    } else {
      // Below threshold — check cooldown
      unsigned long timeSinceMovement = millis() - lastMovementTime;
      if (timeSinceMovement < MOVEMENT_COOLDOWN_MS) {
        // In cooldown window: decay linearly from last value toward 0
        float decayFactor = 1.0 - ((float)timeSinceMovement / (float)MOVEMENT_COOLDOWN_MS);
        movement = mv_smooth * decayFactor;
      } else {
        // Fully settled: report 0
        movement = 0.0;
      }
    }

    // --- Exponential smoothing ---
    // HR: light smoothing (0.15) — simulation is already organic, heavy smoothing would flatten it
    float alpha_hr = 0.15;
    hr_smooth = (alpha_hr * heartRate) + ((1.0 - alpha_hr) * hr_smooth);
    // LT: moderate smoothing (0.3) — real ADC sensor needs some noise reduction
    float alpha_lt = 0.3;
    lt_smooth = (alpha_lt * lightLevel) + ((1.0 - alpha_lt) * lt_smooth);
    // Movement: less smoothing so real hits register quickly, more decay when quiet
    float mv_alpha = (movement > mv_smooth) ? 0.8 : 0.2;
    mv_smooth = (mv_alpha * movement) + ((1.0 - mv_alpha) * mv_smooth);
    if (mv_smooth < 0.05) mv_smooth = 0.0; // snap to zero to avoid creep

    // --- Send CSV over USB Serial ---
    // Format: heart_rate,movement,light
    Serial.print((int)hr_smooth);
    Serial.print(",");
    Serial.print(mv_smooth, 2);
    Serial.print(",");
    Serial.println((int)lt_smooth);

    lastTime = millis();
  }
}
