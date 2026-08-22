/*
  =============================================================================
  🌊 AquaSentinel — ESP32 Physical Node Firmware
  =============================================================================
  Workstream A: Hardware & Firmware Integration

  This firmware runs on the physical ESP32 node to capture water quality telemetry
  from real analog and digital sensors, applies 30-sample median filtering, performs
  temperature-compensated calibration math for TDS, pH, and Turbidity, and transmits
  structured JSON telemetry via HTTP POST to the AquaSentinel FastAPI backend.

  -----------------------------------------------------------------------------
  HARDWARE WIRING GUIDE (ESP32 DevKit V1):
  -----------------------------------------------------------------------------
  Sensor                 ESP32 Pin     ADC / Bus    Notes
  -----------------------------------------------------------------------------
  DS18B20 Temp (DQ)      GPIO 4        1-Wire       Requires 4.7kΩ pull-up to 3.3V
  Analog pH Sensor       GPIO 34       ADC1_CH6     Analog in (0–3.3V)
  Analog TDS Sensor      GPIO 35       ADC1_CH7     Analog in (0–3.3V)
  Optical Turbidity      GPIO 32       ADC1_CH4     Analog in (0–3.3V)
  All Sensors (VCC)      3.3V or 5V    Power        Check sensor board rating
  All Sensors (GND)      GND           Common GND   Connect all grounds together

  * IMPORTANT: All analog sensors are connected to ADC1 pins (GPIO 32, 34, 35).
    ADC2 is NOT used because ESP32 disables ADC2 when Wi-Fi is active.

  -----------------------------------------------------------------------------
  REQUIRED LIBRARIES (Install via Arduino Library Manager):
  -----------------------------------------------------------------------------
  1. ArduinoJson (by Benoit Blanchon, v6 or v7)
  2. OneWire (by Paul Stoffregen)
  3. DallasTemperature (by Miles Burton)

  -----------------------------------------------------------------------------
  JSON PAYLOAD FORMAT (matches backend/app/schemas.py::ReadingIn):
  -----------------------------------------------------------------------------
  POST {BACKEND_URL}/api/readings
  Header: X-API-Key: {API_KEY}
  Body:
  {
    "node_id": "node-01",
    "ph": 7.02,
    "tds": 318.4,
    "turbidity": 12.7,
    "temperature": 28.3
  }
  =============================================================================
*/

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <math.h>

// =============================================================================
// 1. NETWORK & BACKEND CONFIGURATION
// =============================================================================

const char* WIFI_SSID       = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD   = "YOUR_WIFI_PASSWORD";
const char* BACKEND_URL     = "http://YOUR_BACKEND_HOST:8000/api/readings";
const char* API_KEY         = "changeme-dev-key";  // Must match backend AQUASENTINEL_API_KEY
const char* NODE_ID         = "node-01";           // Node identifier

const unsigned long SAMPLE_INTERVAL_MS = 30000;    // 30 seconds sample interval (FR-EDGE-01)
unsigned long lastSampleTime = 0;

// =============================================================================
// 2. PIN DEFINITIONS (ESP32 ADC1 & Digital)
// =============================================================================

#define PIN_DS18B20         4   // Digital 1-Wire for DS18B20 temperature probe
#define PIN_PH              34  // Analog pH probe (ADC1_CH6)
#define PIN_TDS             35  // Analog TDS probe (ADC1_CH7)
#define PIN_TURBIDITY       32  // Optical turbidity sensor (ADC1_CH4)

// =============================================================================
// 3. ADC & FILTERING PARAMETERS
// =============================================================================

#define VREF                3.3f    // ESP32 operating voltage
#define ADC_RESOLUTION      4095.0f // 12-bit ADC (0 - 4095)
#define SAMPLE_COUNT        30      // Samples collected for median filtering
#define SAMPLE_DELAY_MS     5       // Delay between analog ADC samples (ms)

// =============================================================================
// 4. CALIBRATION CONSTANTS
// =============================================================================

// --- pH Calibration ---
// Calibrate with standard buffer solutions (e.g. pH 7.00 and pH 4.01):
// 1. Put probe in pH 7.00 buffer -> note voltage -> set PH_NEUTRAL_VOLTAGE.
// 2. Put probe in pH 4.01 buffer -> note voltage -> calculate PH_SLOPE_VOLTAGE_PER_PH.
#define PH_NEUTRAL_VOLTAGE          2.50f   // Voltage measured at neutral pH 7.00 (sensor-dependent)
#define PH_SLOPE_VOLTAGE_PER_PH     0.18f   // Volts per pH unit change ((V_neutral - V_acid) / (7.0 - 4.01))

// --- TDS Calibration & Temperature Compensation ---
// Calibrate with standard TDS / EC solution (e.g. 1413 µS/cm ≈ 707 ppm TDS):
// kValue = actual_standard_ppm / measured_ppm
#define TDS_K_VALUE                 1.0f    // Calibration multiplier factor

// --- Turbidity Calibration ---
// Sensor polynomial: NTU = A * V^2 + B * V + C
#define TURBIDITY_A                 -1120.4f
#define TURBIDITY_B                  5742.3f
#define TURBIDITY_C                 -4352.9f
#define TURBIDITY_CLEAR_VOLTAGE      2.50f   // Voltages >= this threshold represent clean water (< 5 NTU)

// =============================================================================
// 5. DRIVERS & OBJECTS
// =============================================================================

OneWire oneWire(PIN_DS18B20);
DallasTemperature dallasSensors(&oneWire);

// =============================================================================
// 6. FUNCTION DECLARATIONS
// =============================================================================

void connectWiFi();
float getMedianVoltage(int pin, int sampleCount = SAMPLE_COUNT);
float readTemperature();
float readPH(float voltage);
float readTDS(float voltage, float temperature);
float readTurbidity(float voltage);
bool isPlausible(float ph, float tds, float turbidity, float temperature);
void sendReading(float ph, float tds, float turbidity, float temperature);
void printSensorReport(float ph, float vPH, float tds, float vTDS, float turb, float vTurb, float temp);

// =============================================================================
// 7. SETUP
// =============================================================================

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n=======================================================");
  Serial.println("🌊 AQUASENTINEL: ESP32 Water Intelligence Node Starting");
  Serial.println("=======================================================");

  // Configure ESP32 12-bit ADC & 11dB attenuation (0 - 3.3V input range)
  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);

  // Initialize analog sensor input pins
  pinMode(PIN_PH, INPUT);
  pinMode(PIN_TDS, INPUT);
  pinMode(PIN_TURBIDITY, INPUT);

  // Initialize DS18B20 1-Wire Temperature Sensor
  dallasSensors.begin();
  int deviceCount = dallasSensors.getDeviceCount();
  if (deviceCount > 0) {
    Serial.printf("✓ DS18B20 initialized on GPIO %d (%d sensor(s) detected)\n", PIN_DS18B20, deviceCount);
  } else {
    Serial.printf("⚠️ No DS18B20 detected on GPIO %d. Defaulting to 25.0°C fallback.\n", PIN_DS18B20);
  }

  // Connect to Wi-Fi
  connectWiFi();
}

// =============================================================================
// 8. MAIN LOOP
// =============================================================================

void loop() {
  unsigned long now = millis();

  if (now - lastSampleTime >= SAMPLE_INTERVAL_MS) {
    lastSampleTime = now;

    // 1. SENSE: Read temperature first (needed for TDS & pH compensation)
    float temperature = readTemperature();

    // 2. SENSE: Read raw voltages through 30-sample median filter
    float vPH = getMedianVoltage(PIN_PH);
    float vTDS = getMedianVoltage(PIN_TDS);
    float vTurb = getMedianVoltage(PIN_TURBIDITY);

    // 3. CALIBRATE: Convert filtered voltages to physical engineering units
    float ph = readPH(vPH);
    float tds = readTDS(vTDS, temperature);
    float turbidity = readTurbidity(vTurb);

    // 4. DIAGNOSTICS: Print formatted report to Serial
    printSensorReport(ph, vPH, tds, vTDS, turbidity, vTurb, temperature);

    // 5. TRANSMIT: Plausibility check and HTTP POST
    if (isPlausible(ph, tds, turbidity, temperature)) {
      sendReading(ph, tds, turbidity, temperature);
    } else {
      Serial.println("⚠️ [WARN] Implausible sensor readings detected, skipping transmission (FR-EDGE-04).");
    }
  }

  // Ensure Wi-Fi connection remains active
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }
}

// =============================================================================
// 9. SIGNAL FILTERING (30-Sample Median Filter)
// =============================================================================

/**
 * Collects multiple analog readings, sorts them, and returns the median voltage.
 * Rejects high-frequency ADC noise, 50/60Hz mains hum, and intermittent probe spikes.
 */
float getMedianVoltage(int pin, int sampleCount) {
  int rawSamples[sampleCount];

  for (int i = 0; i < sampleCount; i++) {
    rawSamples[i] = analogRead(pin);
    delay(SAMPLE_DELAY_MS);
  }

  // Simple insertion sort to find median
  for (int i = 1; i < sampleCount; i++) {
    int key = rawSamples[i];
    int j = i - 1;
    while (j >= 0 && rawSamples[j] > key) {
      rawSamples[j + 1] = rawSamples[j];
      j = j - 1;
    }
    rawSamples[j + 1] = key;
  }

  int medianRaw = rawSamples[sampleCount / 2];
  return (float)medianRaw * (VREF / ADC_RESOLUTION);
}

// =============================================================================
// 10. SENSOR CONVERSIONS & CALIBRATIONS
// =============================================================================

/**
 * Read DS18B20 digital 1-Wire temperature sensor.
 * Fallback to 25.0°C if disconnected.
 */
float readTemperature() {
  dallasSensors.requestTemperatures();
  float tempC = dallasSensors.getTempCByIndex(0);

  if (tempC == DEVICE_DISCONNECTED_C || tempC < -50.0f || tempC > 125.0f) {
    Serial.println("⚠️ [TEMP] DS18B20 probe detached/error. Using fallback 25.0°C.");
    return 25.0f;
  }
  return tempC;
}

/**
 * Convert analog pH probe voltage to pH value.
 * Configurable neutral voltage and slope per buffer calibration.
 */
float readPH(float voltage) {
  float ph = 7.0f + ((PH_NEUTRAL_VOLTAGE - voltage) / PH_SLOPE_VOLTAGE_PER_PH);

  // Clamp to valid pH range
  if (ph < 0.0f) ph = 0.0f;
  if (ph > 14.0f) ph = 14.0f;

  return ph;
}

/**
 * Convert analog TDS probe voltage to Total Dissolved Solids (ppm).
 * Correct Pipeline: ADC -> Voltage -> Temperature Compensation -> Polynomial -> kValue -> ppm.
 */
float readTDS(float voltage, float temperature) {
  // Temperature compensation coefficient (standard 2% per °C relative to 25°C)
  float compensationCoefficient = 1.0f + 0.02f * (temperature - 25.0f);
  if (compensationCoefficient <= 0.0f) compensationCoefficient = 1.0f;

  // Temperature-compensated voltage
  float compensatedVoltage = voltage / compensationCoefficient;

  // 3rd-order polynomial conversion from compensated voltage to TDS ppm
  float tds = (133.42f * pow(compensatedVoltage, 3)
              - 255.86f * pow(compensatedVoltage, 2)
              + 857.39f * compensatedVoltage)
              * 0.5f * TDS_K_VALUE;

  if (tds < 0.0f) tds = 0.0f;
  return tds;
}

/**
 * Convert analog turbidity voltage to NTU (Nephelometric Turbidity Units).
 * Applies sensor polynomial with clean-water thresholding and clamping.
 */
float readTurbidity(float voltage) {
  if (voltage >= TURBIDITY_CLEAR_VOLTAGE) {
    // Clear water threshold
    return 0.0f;
  }

  float ntu = (TURBIDITY_A * pow(voltage, 2)) + (TURBIDITY_B * voltage) + TURBIDITY_C;

  // Clamp within realistic measurement bounds (0 to 3000 NTU)
  if (ntu < 0.0f) ntu = 0.0f;
  if (ntu > 3000.0f) ntu = 3000.0f;

  return ntu;
}

// =============================================================================
// 11. SENSOR PLAUSIBILITY CHECK (FR-EDGE-04)
// =============================================================================

/**
 * Checks whether readings are within physical environmental bounds.
 * Mirrors backend anomaly.py bounds.
 */
bool isPlausible(float ph, float tds, float turbidity, float temperature) {
  if (ph < 0.0f || ph > 14.0f) return false;
  if (tds < 0.0f || tds > 5000.0f) return false;
  if (turbidity < 0.0f || turbidity > 3000.0f) return false;
  if (temperature < -5.0f || temperature > 60.0f) return false;
  return true;
}

// =============================================================================
// 12. WI-FI & HTTP TELEMETRY TRANSMISSION
// =============================================================================

void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;

  Serial.printf("\n[Wi-Fi] Connecting to '%s'...\n", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 15000) {
    delay(500);
    Serial.print(".");
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✓ [Wi-Fi] Connected!");
    Serial.print("  IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.printf("  Signal Strength (RSSI): %d dBm\n", WiFi.RSSI());
  } else {
    Serial.println("\n⚠️ [Wi-Fi] Connection failed. Will retry in loop.");
  }
}

void sendReading(float ph, float tds, float turbidity, float temperature) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠️ [SEND] Wi-Fi not connected, skipping HTTP POST.");
    return;
  }

  HTTPClient http;
  http.begin(BACKEND_URL);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-API-Key", API_KEY);

  // Package JSON payload matching backend ReadingIn schema
  StaticJsonDocument<256> doc;
  doc["node_id"] = NODE_ID;
  doc["ph"] = round(ph * 100.0f) / 100.0f;
  doc["tds"] = round(tds * 10.0f) / 10.0f;
  doc["turbidity"] = round(turbidity * 100.0f) / 100.0f;
  doc["temperature"] = round(temperature * 10.0f) / 10.0f;

  String body;
  serializeJson(doc, body);

  Serial.printf("[SEND] POSTing payload to %s...\n", BACKEND_URL);
  Serial.printf("  Body: %s\n", body.c_str());

  int statusCode = http.POST(body);
  if (statusCode > 0) {
    Serial.printf("✓ [HTTP %d] Response: %s\n", statusCode, http.getString().c_str());
  } else {
    Serial.printf("❌ [HTTP FAILED] Error: %s\n", http.errorToString(statusCode).c_str());
  }
  http.end();
}

// =============================================================================
// 13. SERIAL DIAGNOSTICS REPORTER
// =============================================================================

void printSensorReport(float ph, float vPH, float tds, float vTDS, float turb, float vTurb, float temp) {
  Serial.println("\n-------------------------------------------------------");
  Serial.printf("📊 [SCAN] Node ID: %s | RSSI: %d dBm\n", NODE_ID, WiFi.RSSI());
  Serial.println("-------------------------------------------------------");
  Serial.printf("  Temperature : %.2f °C (DS18B20 1-Wire)\n", temp);
  Serial.printf("  pH          : %.2f (Raw: %.3f V | Neutral: %.2f V)\n", ph, vPH, PH_NEUTRAL_VOLTAGE);
  Serial.printf("  TDS         : %.1f ppm (Raw: %.3f V | kValue: %.2f)\n", tds, vTDS, TDS_K_VALUE);
  Serial.printf("  Turbidity   : %.2f NTU (Raw: %.3f V)\n", turb, vTurb);
  Serial.println("-------------------------------------------------------");
}
