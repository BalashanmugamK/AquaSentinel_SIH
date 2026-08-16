/*
  AquaSentinel - ESP32 Node Firmware Skeleton
  Workstream A (Hardware & Firmware) - owner: Sudhish.

  This is a STARTING POINT, not final firmware: it wires up Wi-Fi + HTTP
  POST with the exact JSON payload the backend expects (see
  backend/app/schemas.py::ReadingIn), plus stubs for the four sensor
  reads and a basic plausibility check. Fill in the actual sensor driver
  calls / calibration math for pH, TDS/EC, turbidity, and temperature.

  Payload sent to POST {BACKEND_URL}/api/readings :
  {
    "node_id": "node-01",
    "ph": 7.1,
    "tds": 280,
    "turbidity": 1.2,
    "temperature": 27.1
  }
  (timestamp is optional - backend stamps server time if omitted, which is
  fine for the prototype since ESP32 doesn't need an RTC.)
*/

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ---------- Config - move to a secrets header before committing ----------
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* BACKEND_URL = "http://YOUR_BACKEND_HOST:8000/api/readings";
const char* API_KEY = "changeme-dev-key";  // must match backend AQUASENTINEL_API_KEY
const char* NODE_ID = "node-01";

const unsigned long SAMPLE_INTERVAL_MS = 30000;  // 30s, per FR-EDGE-01 (30-60s range)
unsigned long lastSampleTime = 0;

// ---------- Sensor pins (adjust to your wiring) ----------
const int PH_PIN = 34;
const int TDS_PIN = 35;
const int TURBIDITY_PIN = 32;
const int TEMP_PIN = 33;  // e.g. DS18B20 on OneWire, or analog thermistor

void setup() {
  Serial.begin(115200);
  connectWiFi();
}

void loop() {
  unsigned long now = millis();
  if (now - lastSampleTime >= SAMPLE_INTERVAL_MS) {
    lastSampleTime = now;

    float ph = readPH();
    float tds = readTDS();
    float turbidity = readTurbidity();
    float temperature = readTemperature();

    if (isPlausible(ph, tds, turbidity, temperature)) {
      sendReading(ph, tds, turbidity, temperature);
    } else {
      Serial.println("[warn] implausible reading, skipping transmission (FR-EDGE-04)");
    }
  }

  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }
}

void connectWiFi() {
  Serial.printf("Connecting to Wi-Fi '%s'...\n", WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 15000) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(WiFi.status() == WL_CONNECTED ? "\nConnected." : "\nWi-Fi connect failed, will retry.");
}

// ---------- Sensor reads - TODO: replace with real calibration ----------

float readPH() {
  int raw = analogRead(PH_PIN);
  // TODO: apply pH probe calibration curve (buffer solutions per SRS FR-EDGE-02)
  float voltage = raw * (3.3 / 4095.0);
  float ph = 7.0 + ((2.5 - voltage) / 0.18);  // placeholder linear approximation
  return ph;
}

float readTDS() {
  int raw = analogRead(TDS_PIN);
  // TODO: apply TDS/EC calibration per module datasheet + reference solution
  float voltage = raw * (3.3 / 4095.0);
  float tds = (voltage / 3.3) * 1000.0;  // placeholder
  return tds;
}

float readTurbidity() {
  int raw = analogRead(TURBIDITY_PIN);
  // TODO: apply turbidity calibration per sensor characteristics
  float voltage = raw * (3.3 / 4095.0);
  float ntu = (3.3 - voltage) * 100.0;  // placeholder, clamp to >= 0 below
  return ntu < 0 ? 0 : ntu;
}

float readTemperature() {
  int raw = analogRead(TEMP_PIN);
  // TODO: replace with DS18B20 (OneWire) or thermistor formula
  float voltage = raw * (3.3 / 4095.0);
  float tempC = voltage * 100.0;  // placeholder
  return tempC;
}

// ---------- Basic plausibility check (mirrors backend anomaly.py ranges) ----------

bool isPlausible(float ph, float tds, float turbidity, float temperature) {
  if (ph < 0 || ph > 14) return false;
  if (tds < 0 || tds > 5000) return false;
  if (turbidity < 0 || turbidity > 3000) return false;
  if (temperature < -5 || temperature > 60) return false;
  return true;
}

// ---------- Transmission ----------

void sendReading(float ph, float tds, float turbidity, float temperature) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[warn] Wi-Fi not connected, skipping send");
    return;
  }

  HTTPClient http;
  http.begin(BACKEND_URL);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-API-Key", API_KEY);

  StaticJsonDocument<256> doc;
  doc["node_id"] = NODE_ID;
  doc["ph"] = ph;
  doc["tds"] = tds;
  doc["turbidity"] = turbidity;
  doc["temperature"] = temperature;

  String body;
  serializeJson(doc, body);

  int statusCode = http.POST(body);
  if (statusCode > 0) {
    Serial.printf("POST -> %d\n", statusCode);
    Serial.println(http.getString());
  } else {
    Serial.printf("[error] POST failed: %s\n", http.errorToString(statusCode).c_str());
  }
  http.end();
}
