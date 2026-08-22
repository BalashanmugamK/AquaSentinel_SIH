#include <OneWire.h>
#include <DallasTemperature.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Wire.h>

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>


#define LED 2

#define PH_PIN 36       // VP = GPIO 36
#define TURB_PIN 34     // GPIO 34
#define TDS_PIN 32 // TDS PIN 

#define TEMP_PIN 4

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

#define OLED_SDA 21
#define OLED_SCL 22

const char* ssid = "CMFSSN";
const char* password = "meatcmf24";

const char* serverUrl = "https://waterqualityinspector.onrender.com/inspect";

const char* serverUrlPolling = "https://sih-api-db.onrender.com/latestValuePolling";


Adafruit_SSD1306 display(
  SCREEN_WIDTH,
  SCREEN_HEIGHT,
  &Wire,
  -1
);

String text = "AquaSentinel";

OneWire oneWire(TEMP_PIN);
DallasTemperature sensors(&oneWire);


void connectWiFi() {

  WiFi.begin(ssid, password);

  Serial.print("Connecting to WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("WiFi Connected!");

  Serial.print("ESP32 IP Address: ");
  Serial.println(WiFi.localIP());
}


void setup() {
  Serial.begin(115200);
  connectWiFi();
  //pinMode(LED, OUTPUT);

  Wire.begin(OLED_SDA, OLED_SCL);

  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("OLED not found!");
    while (true);
  }
  
  sensors.begin();
  // ESP32 ADC resolution: 0–4095
  analogReadResolution(12);
}


void scrollOLED(String staticText, String scrollText) {

  int textSize = 1.5;
  int textWidth = scrollText.length() * 6 * textSize;

  for (int x = SCREEN_WIDTH; x > -textWidth; x--) {

    display.clearDisplay();

    display.setTextSize(textSize);
    display.setTextColor(WHITE);
    display.setTextWrap(false);

    // First line - Static
    display.setCursor(0, 5);
    display.print(staticText);

    // Second line - Scrolling
    display.setCursor(x, 25);
    display.print(scrollText);

    display.display();

    delay(30);
  }
}


void sendSensorData(
  float phVoltage,
  int turbidity,
  float tdsVoltage,
  float temperatureC
) {

  if (WiFi.status() == WL_CONNECTED) {

    HTTPClient http;

    // Create JSON
    JsonDocument jsonDoc;

    jsonDoc["ph"] = phVoltage;
    jsonDoc["turbidity"] = turbidity;
    jsonDoc["tds"] = tdsVoltage;
    jsonDoc["temperature"] = temperatureC;

    String jsonData;
    serializeJson(jsonDoc, jsonData);

    // Print data being sent
    Serial.println("\n========== SENDING DATA ==========");
    Serial.println(jsonData);

    // API call
    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");

    int httpResponseCode = http.POST(jsonData);

    // Print HTTP status code
    Serial.print("HTTP Response Code: ");
    Serial.println(httpResponseCode);

    // ==============================
    // PRINT RESPONSE FROM API
    // ==============================
    if (httpResponseCode > 0) {

      String response = http.getString();

      Serial.println("\n========== API RESPONSE ==========");
      Serial.println(response);
      Serial.println("==================================");

    } else {

      Serial.print("HTTP Request Failed. Error: ");
      Serial.println(http.errorToString(httpResponseCode));

    }

    http.end();

  } else {

    Serial.println("WiFi not connected!");
  }
}


void sendSensorDataRaw(
  float ph,
  float tds,
  float temperature,
  int turbidity
) {
  // Check Wi-Fi
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected!");
    return;
  }

  HTTPClient http;

  // Create JSON manually
  String jsonData = "{";

  jsonData += "\"ph\":" + String(ph, 2) + ",";
  jsonData += "\"tds\":" + String(tds, 2) + ",";
  jsonData += "\"temperature\":" + String(temperature, 2) + ",";
  jsonData += "\"turbidity\":" + String(turbidity);

  jsonData += "}";

  // Print outgoing JSON
  Serial.println("\n========== SENDING TO API ==========");
  Serial.println(jsonData);

  // Connect to API endpoint
  http.begin(serverUrlPolling);

  // Specify JSON content
  http.addHeader("Content-Type", "application/json");

  // Send POST request
  int httpResponseCode = http.POST(jsonData);

  // Print HTTP status
  Serial.print("HTTP Response Code: ");
  Serial.println(httpResponseCode);

  // Print API response
  if (httpResponseCode > 0) {

    String response = http.getString();

    Serial.println("========== API RESPONSE ==========");
    Serial.println(response);
    Serial.println("==================================");

  } else {

    Serial.print("Request failed: ");
    Serial.println(http.errorToString(httpResponseCode));
  }

  // Close connection
  http.end();
}


void loop() {

  // =========================
  // pH SENSOR
  // =========================
  int rawValue = analogRead(PH_PIN);

  float phVoltage = rawValue * 3.3 / 4095.0;

  Serial.print("pH Raw ADC: ");
  Serial.print(rawValue);

  Serial.print(" | pH Sensor Voltage: ");
  Serial.print(phVoltage, 3);
  Serial.println(" V");


  // =========================
  // TURBIDITY SENSOR
  // =========================
  int turbRawValue = analogRead(TURB_PIN);

  float turbVoltage = turbRawValue * 3.3 / 4095.0;

  // Temporary turbidity scale: 1 to 5
  int turbidity = map(turbRawValue, 0, 2800, 5, 1);

  // Prevent values outside the expected range
  turbidity = constrain(turbidity, 1, 5);

  Serial.print("Turbidity Raw ADC: ");
  Serial.print(turbRawValue);

  Serial.print(" | Voltage: ");
  Serial.print(turbVoltage, 3);
  Serial.print(" V");

  Serial.print(" | Turbidity Level: ");
  Serial.println(turbidity);


  Serial.println("---------------------------");

  int tdsRaw = analogRead(TDS_PIN);

  // Approximate voltage
  float tdsVoltage = tdsRaw * 3.3 / 4095.0;

  Serial.print("TDS Raw ADC: ");
  Serial.print(tdsRaw);

  Serial.print(" | Voltage: ");
  Serial.print(tdsVoltage, 3);
  Serial.println(" V");


  Serial.println("--------TEMPERATURE--------");

  sensors.requestTemperatures();

  float temperatureC = sensors.getTempCByIndex(0);

  Serial.print("Temperature: ");
  Serial.print(temperatureC);
  Serial.println(" °C");

  // =========================
// RUNNING TEXT
// =========================

  scrollOLED(
    "Aqua SentinelX",
    "The Best Water Quality Monitoring System"
  );

  sendSensorDataRaw(
    phVoltage,
    tdsRaw,
    temperatureC,
    turbidity
  );

  delay(100);
}
