/*
 * AquaSentinel — ESP32 Water Intelligence Telemetry Firmware
 *
 * Hardware / Simulation Setup:
 * - DS18B20 Digital Temperature Sensor: Pin 4
 * - pH Analog Simulation Potentiometer: Pin 34
 * - Turbidity Analog Simulation Potentiometer: Pin 35
 * - TDS / EC Analog Simulation Potentiometer: Pin 32
 *
 * Outbound Internet Transport:
 * - WiFi: "Wokwi-GUEST"
 * - HTTPS POST to ngrok public tunnel
 * - FastAPI backend on localhost:8000
 */

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// =========================================================================
// CONFIGURATION
// =========================================================================

const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASSWORD = "";

// Active ngrok tunnel
const char* BACKEND_TELEMETRY_URL =
    "https://resisting-outflank-rippling.ngrok-free.dev/api/telemetry";

const char* DEVICE_ID = "AQUA-01";

const unsigned long TELEMETRY_INTERVAL_MS = 5000;

// =========================================================================
// HARDWARE PIN DEFINITIONS
// =========================================================================

#define PIN_ONEWIRE_TEMP 4
#define PIN_POT_PH 34
#define PIN_POT_TURBIDITY 35
#define PIN_POT_EC 32

// =========================================================================
// DS18B20
// =========================================================================

OneWire oneWire(PIN_ONEWIRE_TEMP);
DallasTemperature tempSensor(&oneWire);

unsigned long lastSendTime = 0;

// =========================================================================
// SETUP
// =========================================================================

void setup() {

  Serial.begin(115200);
  delay(1000);

  Serial.println("\n=======================================================");
  Serial.println("🌊 AQUASENTINEL: ESP32 Water Intelligence Node Starting");
  Serial.println("=======================================================");

  // -----------------------------------------------------------------------
  // Initialize analog pins
  // -----------------------------------------------------------------------

  pinMode(PIN_POT_PH, INPUT);
  pinMode(PIN_POT_TURBIDITY, INPUT);
  pinMode(PIN_POT_EC, INPUT);

  // -----------------------------------------------------------------------
  // Initialize DS18B20
  // -----------------------------------------------------------------------

  tempSensor.begin();

  Serial.println(
      "✓ DS18B20 Temperature sensor initialized on GPIO 4"
  );

  // -----------------------------------------------------------------------
  // Connect to Wi-Fi
  // -----------------------------------------------------------------------

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

    Serial.println(
        "\n⚠️ Wi-Fi connection timeout. Retrying in loop..."
    );
  }
}

// =========================================================================
// SENSOR FUNCTIONS
// =========================================================================

// -------------------------------------------------------------------------
// Simulated pH
// ADC 0-4095 → pH 0-14
// -------------------------------------------------------------------------

float readSimulatedPH() {

  int raw = analogRead(PIN_POT_PH);

  return (float)raw * 14.0 / 4095.0;
}

// -------------------------------------------------------------------------
// Simulated Turbidity
// ADC 0-4095 → 0-100 NTU
// -------------------------------------------------------------------------

float readSimulatedTurbidity() {

  int raw = analogRead(PIN_POT_TURBIDITY);

  return (float)raw * 100.0 / 4095.0;
}

// -------------------------------------------------------------------------
// Simulated EC / TDS
// ADC 0-4095 → 0-2000 µS/cm
// -------------------------------------------------------------------------

float readSimulatedEC() {

  int raw = analogRead(PIN_POT_EC);

  return (float)raw * 2000.0 / 4095.0;
}

// -------------------------------------------------------------------------
// DS18B20 Temperature
// -------------------------------------------------------------------------

float readTemperature() {

  tempSensor.requestTemperatures();

  float tempC = tempSensor.getTempCByIndex(0);

  if (
      tempC == DEVICE_DISCONNECTED_C ||
      tempC < -50.0
  ) {

    // Simulator fallback
    return 26.5;
  }

  return tempC;
}

// =========================================================================
// LOOP
// =========================================================================

void loop() {

  unsigned long currentMillis = millis();

  if (
      currentMillis - lastSendTime >=
      TELEMETRY_INTERVAL_MS
  ) {

    lastSendTime = currentMillis;

    // =====================================================================
    // 1. SENSE
    // =====================================================================

    float ph = readSimulatedPH();
    float turb = readSimulatedTurbidity();
    float ec = readSimulatedEC();
    float temp = readTemperature();

    Serial.println("\n--- [SENSE] New Sensor Scan ---");

    Serial.printf(
        "  pH:          %.2f\n",
        ph
    );

    Serial.printf(
        "  Turbidity:   %.2f NTU\n",
        turb
    );

    Serial.printf(
        "  EC / TDS:    %.1f uS/cm\n",
        ec
    );

    Serial.printf(
        "  Temperature: %.2f C\n",
        temp
    );

    // =====================================================================
    // 2. PACKAGE JSON
    // =====================================================================

    String jsonPayload = "{";

    jsonPayload +=
        "\"device_id\":\"" +
        String(DEVICE_ID) +
        "\",";

    jsonPayload +=
        "\"ph\":" +
        String(ph, 2) +
        ",";

    jsonPayload +=
        "\"turbidity\":" +
        String(turb, 2) +
        ",";

    jsonPayload +=
        "\"ec\":" +
        String(ec, 1) +
        ",";

    jsonPayload +=
        "\"temperature\":" +
        String(temp, 2);

    jsonPayload += "}";

    // =====================================================================
    // 3. NETWORK CHECK + HTTPS POST
    // =====================================================================

    if (WiFi.status() == WL_CONNECTED) {

      // -------------------------------------------------------------------
      // TEST 1: Can Wokwi make an outbound TCP connection?
      // -------------------------------------------------------------------

      WiFiClient testClient;

      Serial.println(
          "  [NET TEST] Connecting to example.com..."
      );

      if (testClient.connect("example.com", 80)) {

        Serial.println(
            "  ✅ [NET TEST] Internet TCP connection works!"
        );

        testClient.stop();

      } else {

        Serial.println(
            "  ❌ [NET TEST] Internet TCP connection FAILED!"
        );
      }

      // -------------------------------------------------------------------
      // TEST 2: HTTPS connection to ngrok
      // -------------------------------------------------------------------

      WiFiClientSecure client;

      // Wokwi/testing only:
      // Skip certificate verification.
      client.setInsecure();

      HTTPClient http;

      Serial.println(
          "  [HTTPS TEST] Initializing ngrok connection..."
      );

      if (
          http.begin(
              client,
              BACKEND_TELEMETRY_URL
          )
      ) {

        http.addHeader(
            "Content-Type",
            "application/json"
        );

        Serial.print(
            "  [SEND] POSTing to "
        );

        Serial.println(
            BACKEND_TELEMETRY_URL
        );

        // ---------------------------------------------------------------
        // POST telemetry
        // ---------------------------------------------------------------

        int httpResponseCode =
            http.POST(jsonPayload);

        // ---------------------------------------------------------------
        // Successful HTTP response
        // ---------------------------------------------------------------

        if (httpResponseCode > 0) {

          String response =
              http.getString();

          Serial.printf(
              "  [STORE/DETECT] HTTP %d: %s\n",
              httpResponseCode,
              response.c_str()
          );

        }

        // ---------------------------------------------------------------
        // Failed HTTP request
        // ---------------------------------------------------------------

        else {

          Serial.printf(
              "  ⚠️ [SEND FAILED] Error code: %d (%s)\n",
              httpResponseCode,
              http.errorToString(
                  httpResponseCode
              ).c_str()
          );

          Serial.println(
              "  💡 Check ngrok and backend availability."
          );
        }

        http.end();

      } else {

        Serial.println(
            "  ⚠️ [HTTPS] Failed to initialize connection"
        );
      }

    } else {

      // ===================================================================
      // Wi-Fi disconnected
      // ===================================================================

      Serial.println(
          "  ⚠️ Wi-Fi disconnected. Reconnecting..."
      );

      WiFi.reconnect();
    }
  }

  delay(50);
}