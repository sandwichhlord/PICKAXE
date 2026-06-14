#include <Wire.h>
#include "BluetoothSerial.h"

BluetoothSerial SerialBT;

// smoothing for acc only
float sX = 0, sY = 0, sZ = 0;
const float alpha_accel = 0.15; 

// edge computing impact vars
const int IMPACT_LED_PIN = 2;   
const float IMPACT_THRESHOLD = 2.5;
unsigned long impactTimer = 0;      

void setup() {
  Serial.begin(115200);
  SerialBT.begin("PICKAXE_ESP32"); 
  Serial.println("Bluetooth Started!");

  pinMode(IMPACT_LED_PIN, OUTPUT);

  Wire.begin(21, 22);
  delay(500);

  Wire.beginTransmission(0x68);
  Wire.write(0x6B); Wire.write(0);
  Wire.endTransmission(true);

  Wire.beginTransmission(0x57);
  Wire.write(0x09); Wire.write(0x40); delay(100);
  Wire.beginTransmission(0x57);
  Wire.write(0x09); Wire.write(0x03); 
  Wire.endTransmission();
  Wire.beginTransmission(0x57);
  Wire.write(0x0C); Wire.write(0xFF); 
  Wire.endTransmission();
  Wire.beginTransmission(0x57);
  Wire.write(0x0D); Wire.write(0xFF); 
  Wire.endTransmission();
}

void loop() {
  Wire.beginTransmission(0x68);
  Wire.write(0x3B); 
  Wire.endTransmission(false);
  Wire.requestFrom(0x68, 8, true); 
  
  int16_t rawX = Wire.read() << 8; rawX |= Wire.read();
  int16_t rawY = Wire.read() << 8; rawY |= Wire.read();
  int16_t rawZ = Wire.read() << 8; rawZ |= Wire.read();
  int16_t rawTemp = Wire.read() << 8; rawTemp |= Wire.read();

  float accX = rawX / 16384.0;
  float accY = rawY / 16384.0;
  float accZ = rawZ / 16384.0;
  float tempC = (rawTemp / 340.0) + 36.53;

  // acc smoothing
  sX = (sX * (1.0 - alpha_accel)) + (accX * alpha_accel);
  sY = (sY * (1.0 - alpha_accel)) + (accY * alpha_accel);
  sZ = (sZ * (1.0 - alpha_accel)) + (accZ * alpha_accel);

  float currentMag = sqrt((accX * accX) + (accY * accY) + (accZ * accZ));
  
  if (currentMag > IMPACT_THRESHOLD) {
    digitalWrite(IMPACT_LED_PIN, HIGH);
    impactTimer = millis();
  }

  if (millis() - impactTimer > 500) {
    digitalWrite(IMPACT_LED_PIN, LOW);
  }

  Wire.beginTransmission(0x57);
  Wire.write(0x07); 
  Wire.endTransmission(false);
  
  uint32_t rawIR = 0;
  if (Wire.requestFrom(0x57, 3, true) == 3) {
    rawIR = (uint32_t)Wire.read() << 16 | (uint32_t)Wire.read() << 8 | (uint32_t)Wire.read();
    rawIR &= 0x3FFFF;
  }

  // bluetooth comms
  SerialBT.print(rawIR);     SerialBT.print(",");
  SerialBT.print(tempC);     SerialBT.print(",");
  SerialBT.print(accX, 2);     SerialBT.print(",");
  SerialBT.print(accY, 2);     SerialBT.print(",");
  SerialBT.println(accZ, 2);

  delay(50); 
}