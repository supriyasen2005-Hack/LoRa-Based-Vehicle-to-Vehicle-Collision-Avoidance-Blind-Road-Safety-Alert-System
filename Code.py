// =====================================================
// SMART V2V SYSTEM FINAL OLED VERSION
// ESP32 + SX1278 + SH1106 OLED + HC-SR04
// ALERT DISTANCE = 50cm
// CAR01 CODE
// =====================================================

#include <SPI.h>
#include <Wire.h>
#include <LoRa.h>
#include <U8g2lib.h>

// ================= OLED =================
U8G2_SH1106_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0);

// ================= LORA =================
#define LORA_SS     5
#define LORA_RST    14
#define LORA_DIO0   26

#define LORA_SCK    18
#define LORA_MISO   19
#define LORA_MOSI   23

// ================= ULTRASONIC =================
#define TRIG 12
#define ECHO 13

// ================= BUZZER =================
#define BUZZER 25

// ================= BLUE LED =================
#define LED 2

// ================= VEHICLE ID =================
String vehicleID = "CAR01";

// ================= VARIABLES =================
bool vehicleDetected = false;

float distance = 0;

String signalLevel = "NONE";

unsigned long lastReceiveTime = 0;

// =====================================================
// DISTANCE FUNCTION
// =====================================================
float getDistance() {

  digitalWrite(TRIG, LOW);
  delayMicroseconds(5);

  digitalWrite(TRIG, HIGH);
  delayMicroseconds(10);

  digitalWrite(TRIG, LOW);

  long duration = pulseIn(ECHO, HIGH, 50000);

  if(duration <= 0)
    return 999;

  float dist = duration * 0.034 / 2;

  if(dist < 2 || dist > 400)
    return 999;

  return dist;
}

// =====================================================
// OLED DISPLAY FUNCTION
// =====================================================
void drawDisplay(bool alert) {

  u8g2.clearBuffer();

  u8g2.setFont(u8g2_font_6x12_tr);

  // ===== TITLE =====
  u8g2.drawStr(20,10,"SMART V2V");

  // ===== VEHICLE =====
  u8g2.setCursor(0,25);

  u8g2.print("Vehicle:");

  if(vehicleDetected)
    u8g2.print("YES");
  else
    u8g2.print("NO");

  // ===== DISTANCE =====
  u8g2.setCursor(0,40);

  u8g2.print("Dist:");

  u8g2.print(distance);

  u8g2.print("cm");

  // ===== SIGNAL =====
  u8g2.setCursor(0,55);

  u8g2.print("Signal:");

  u8g2.print(signalLevel);

  // ===== ALERT =====
  if(alert) {

    u8g2.setCursor(85,25);

    u8g2.print("ALERT");
  }

  u8g2.sendBuffer();
}

// =====================================================
// LORA INIT
// =====================================================
bool initLoRa() {

  SPI.begin(LORA_SCK, LORA_MISO, LORA_MOSI, LORA_SS);

  LoRa.setPins(LORA_SS, LORA_RST, LORA_DIO0);

  if(!LoRa.begin(433E6)) {

    return false;
  }

  // ===== STABLE SETTINGS =====
  LoRa.setTxPower(20);

  LoRa.setSpreadingFactor(12);

  LoRa.setSignalBandwidth(125E3);

  LoRa.setCodingRate4(5);

  return true;
}

// =====================================================
// SETUP
// =====================================================
void setup() {

  Serial.begin(115200);

  delay(1000);

  // ===== LED =====
  pinMode(LED, OUTPUT);

  // ===== BUZZER =====
  pinMode(BUZZER, OUTPUT);

  // ===== ULTRASONIC =====
  pinMode(TRIG, OUTPUT);

  pinMode(ECHO, INPUT);

  // ===== LED TEST =====
  digitalWrite(LED, HIGH);

  delay(500);

  digitalWrite(LED, LOW);

  // ===== OLED =====
  Wire.begin(21,22);

  delay(500);

  u8g2.begin();

  u8g2.clearBuffer();

  u8g2.setFont(u8g2_font_6x12_tr);

  u8g2.drawStr(15,30,"SYSTEM START");

  u8g2.sendBuffer();

  delay(1500);

  // ===== LORA =====
  bool loraOK = initLoRa();

  if(!loraOK) {

    u8g2.clearBuffer();

    u8g2.drawStr(10,30,"LORA FAILED");

    u8g2.sendBuffer();

    while(1) {

      digitalWrite(LED, HIGH);
      delay(200);

      digitalWrite(LED, LOW);
      delay(200);
    }
  }

  // ===== LORA OK =====
  u8g2.clearBuffer();

  u8g2.drawStr(30,30,"LORA OK");

  u8g2.sendBuffer();

  delay(1500);
}

// =====================================================
// LOOP
// =====================================================
void loop() {

  // ===== BLUE LED BLINK =====
  digitalWrite(LED, HIGH);

  delay(50);

  digitalWrite(LED, LOW);

  // =================================================
  // SEND DATA
  // =================================================
  LoRa.beginPacket();

  LoRa.print(vehicleID);

  LoRa.endPacket();

  // =================================================
  // RECEIVE DATA
  // =================================================
  int packetSize = LoRa.parsePacket();

  if(packetSize) {

    String incoming = "";

    while(LoRa.available()) {

      incoming += (char)LoRa.read();
    }

    // ===== Ignore own packet =====
    if(incoming != vehicleID) {

      vehicleDetected = true;

      lastReceiveTime = millis();

      int rssi = LoRa.packetRssi();

      // ===== SIGNAL LEVEL =====
      if(rssi > -70)
        signalLevel = "NEAR";

      else if(rssi > -90)
        signalLevel = "MID";

      else
        signalLevel = "FAR";
    }
  }

  // =================================================
  // VEHICLE TIMEOUT
  // =================================================
  if(millis() - lastReceiveTime > 3000) {

    vehicleDetected = false;

    signalLevel = "NONE";
  }

  // =================================================
  // DISTANCE CHECK
  // =================================================
  distance = getDistance();

  // =================================================
  // ALERT SYSTEM
  // =================================================
  bool alert = false;

  // ALERT DISTANCE = 50cm
  if(vehicleDetected && distance < 50)
    alert = true;

  // =================================================
  // BUZZER
  // =================================================
  digitalWrite(BUZZER, alert);

  // =================================================
  // OLED DISPLAY
  // =================================================
  drawDisplay(alert);

  // =================================================
  // LOOP DELAY
  // =================================================
  delay(700);
}