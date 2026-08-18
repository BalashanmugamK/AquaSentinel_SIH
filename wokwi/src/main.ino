/*
 * AquaSentinel — ESP32 Water Intelligence Telemetry Firmware
 *
 * Hardware / Simulation Setup:
 * - DS18B20 Digital Temperature Sensor: Pin 4 (with 4.7k pull-up to 3V3)
 * - pH Analog Simulation Potentiometer: Pin 34 (ADC1_CH6)
 * - Turbidity Analog Simulation Potentiometer: Pin 35 (ADC1_CH7)
 * - TDS / EC Analog Simulation Potentiometer: Pin 32 (ADC1_CH4)
 *
 * Outbound Internet Transport:
 * - WiFi: "Wokwi-GUEST" (Free tier outbound gateway)
 * - HTTPS POST to ngrok public tunnel forwarding to FastAPI backend
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// =========================================================================
// CONFIGURATION
// =========================================================================
const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASSWORD = "";

// REPLACE THIS with your active ngrok forwarding URL (e.g. https://abc-123.ngrok-free.app/api/telemetry)
const char* BACKEND_TELEMETRY_URL = "https://your-ngrok-subdomain.ngrok-free.app/api/telemetry";

const char* DEVICE_ID = "AQUA-01";
const unsigned long TELEMETRY_INTERVAL_MS = 5000; // Ingestion rate: 5s

// Hardware Pin Definitions
#define PIN_ONEWIRE_TEMP 4
#define PIN_POT_PH 34
#define PIN_POT_TURBIDITY 35
#define PIN_POT_EC 32

OneWire oneWire(PIN_ONEWIRE_TEMP);
DallasTemperature tempSensor(&oneWire);

unsigned long lastSendTime = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n=======================================================");
  Serial.println("🌊 AQUASENTINEL: ESP32 Water Intelligence Node Starting");
  Serial.println("=======================================================");

  // Initialize analog pins
  pinMode(PIN_POT_PH, INPUT);
  pinMode(PIN_POT_TURBIDITY, INPUT);
  pinMode(PIN_POT_EC, INPUT);

  // Initialize DS18B20 Temperature Sensor
  tempSensor.begin();
  Serial.println("✓ DS18B20 Temperature sensor initialized on GPIO 4");

  // Connect to Wi-Fi
  Serial.print("Connecting to Wi-Fi: ");
  Serial.println(WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD, 6);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✓ Wi-Fi Connected!");
    Serial.print("  IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n⚠️ Wi-Fi connection timeout. Retrying in loop...");
  }
}

// Map ADC raw (0 - 4095) to physical engineering units
float readSimulatedPH() {
  int raw = analogRead(PIN_POT_PH);
  // Linear scaling: 0 -> 0.0 pH, 4095 -> 14.0 pH
  return (float)raw * 14.0 / 4095.0;
}

float readSimulatedTurbidity() {
  int raw = analogRead(PIN_POT_TURBIDITY);
  // Linear scaling: 0 -> 0.0 NTU, 4095 -> 100.0 NTU
  return (float)raw * 100.0 / 4095.0;
}

float readSimulatedEC() {
  int raw = analogRead(PIN_POT_EC);
  // Linear scaling: 0 -> 0.0 µS/cm, 4095 -> 2000.0 µS/cm
  return (float)raw * 2000.0 / 4095.0;
}

float readTemperature() {
  tempSensor.requestTemperatures();
  float tempC = tempSensor.getTempCByIndex(0);
  if (tempC == DEVICE_DISCONNECTED_C || tempC < -50.0) {
    // Default fallback if simulator detached
    return 26.5;
  }
  return tempC;
}

void loop() {
  unsigned long currentMillis = millis();

  if (currentMillis - lastSendTime >= TELEMETRY_INTERVAL_MS) {
    lastSendTime = currentMillis;

    // 1. SENSE
    float ph = readSimulatedPH();
    float turb = readSimulatedTurbidity();
    float ec = readSimulatedEC();
    float temp = readTemperature();

    Serial.println("\n--- [SENSE] New Sensor Scan ---");
    Serial.printf("  pH:          %.2f\n", ph);
    Serial.printf("  Turbidity:   %.2f NTU\n", turb);
    Serial.printf("  EC / TDS:    %.1f uS/cm\n", ec);
    Serial.printf("  Temperature: %.2f C\n", temp);

    // 2. PACKAGE JSON
    String jsonPayload = "{";
    jsonPayload += "\"device_id\":\"" + String(DEVICE_ID) + "\",";
    jsonPayload += "\"ph\":" + String(ph, 2) + ",";
    jsonPayload += "\"turbidity\":" + String(turb, 2) + ",";
    jsonPayload += "\"ec\":" + String(ec, 1) + ",";
    jsonPayload += "\"temperature\":" + String(temp, 2);
    jsonPayload += "}";

    // 3. SEND VIA HTTPS POST
    if (WiFi.status() == WL_CONNECTED) {
      HTTPClient http;
      http.begin(BACKEND_TELEMETRY_URL);
      http.addHeader("Content-Type", "application/json");

      Serial.print("  [SEND] POSTing to ");
      Serial.println(BACKEND_TELEMETRY_URL);

      int httpResponseCode = http.POST(jsonPayload);

      if (httpResponseCode > 0) {
        String response = http.getString();
        Serial.printf("  [STORE/DETECT] HTTP %d: %s\n", httpResponseCode, response.c_str());
      } else {
        Serial.printf("  ⚠️ [SEND FAILED] Error code: %d (%s)\n", httpResponseCode, http.errorToString(httpResponseCode).c_str());
        Serial.println("  💡 Tip: Check if ngrok is active and BACKEND_TELEMETRY_URL matches current tunnel.");
      }
      http.end();
    } else {
      Serial.println("  ⚠️ Wi-Fi disconnected. Reconnecting...");
      WiFi.reconnect();
    }
  }

  delay(50);
}
