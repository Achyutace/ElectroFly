#include "SoftI2C.h"
#include <MadgwickAHRS.h>

#define NUM_SENSORS 4
const char* locations[NUM_SENSORS] = {"thigh_r", "shank_r", "thigh_l", "shank_l"};

#define SDA_PIN 6
#define SCL_PIN 7
SoftI2C myI2C(SDA_PIN, SCL_PIN);

#define MPU_ADDR 0x68
#define MUX_ADDR 0x70

Madgwick filters[NUM_SENSORS];
bool mpu_ready[NUM_SENSORS] = {false};

unsigned long lastUpdate = 0;
const unsigned long interval = 10; // 100Hz
unsigned long start_time;

void selectMuxChannel(uint8_t channel) {
  myI2C.beginTransmission(MUX_ADDR);
  myI2C.write(1 << channel);
  myI2C.endTransmission();
  delay(5);
}

void writeMPU(uint8_t reg, uint8_t data) {
  myI2C.beginTransmission(MPU_ADDR);
  myI2C.write(reg);
  myI2C.write(data);
  myI2C.endTransmission();
}

bool readMPUData(int16_t* ax, int16_t* ay, int16_t* az,
                 int16_t* gx, int16_t* gy, int16_t* gz) {
  myI2C.beginTransmission(MPU_ADDR);
  myI2C.write(0x3B); // Starting from ACCEL_XOUT_H
  if (myI2C.endTransmission() != 0) return false;

  if (myI2C.requestFrom(MPU_ADDR, 14) != 14) return false;

  *ax = (myI2C.read() << 8) | myI2C.read();
  *ay = (myI2C.read() << 8) | myI2C.read();
  *az = (myI2C.read() << 8) | myI2C.read();
  myI2C.read(); myI2C.read(); // TEMP (ignore)
  *gx = (myI2C.read() << 8) | myI2C.read();
  *gy = (myI2C.read() << 8) | myI2C.read();
  *gz = (myI2C.read() << 8) | myI2C.read();

  return true;
}

void setup() {
  Serial.begin(115200);
  myI2C.begin();

  for (int i = 0; i < NUM_SENSORS; i++) {
    selectMuxChannel(i);

    // Wake up MPU6050
    writeMPU(0x6B, 0x00); // Power Management 1
    delay(50);

    // Optionally check WHO_AM_I = 0x68
    myI2C.beginTransmission(MPU_ADDR);
    myI2C.write(0x75);
    myI2C.endTransmission();
    myI2C.requestFrom(MPU_ADDR, 1);
    uint8_t whoami = myI2C.read();

    if (whoami == 0x68) {
      mpu_ready[i] = true;
      filters[i].begin(100.0f);
      Serial.print("✅ MPU6050["); Serial.print(i); Serial.println("] OK");
    } else {
      Serial.print("❌ MPU6050["); Serial.print(i); Serial.println("] init failed!");
    }
  }

  Serial.println("===START===");
  Serial.println("timestamp\tsensor_type\tlocation\tchannel\tvalue_x\tvalue_y\tvalue_z\troll\tpitch\tyaw\traw_signal");
  start_time = millis();
}

void loop() {
  if (millis() - lastUpdate >= interval) {
    lastUpdate = millis();
    unsigned long current_time = millis() - start_time;

    for (int i = 0; i < NUM_SENSORS; i++) {
      if (!mpu_ready[i]) continue;

      selectMuxChannel(i);

      int16_t ax, ay, az, gx, gy, gz;
      if (!readMPUData(&ax, &ay, &az, &gx, &gy, &gz)) continue;

      float ax_f = ax / 16384.0;
      float ay_f = ay / 16384.0;
      float az_f = az / 16384.0;
      float gx_f = gx * DEG_TO_RAD / 131.0;
      float gy_f = gy * DEG_TO_RAD / 131.0;
      float gz_f = gz * DEG_TO_RAD / 131.0;

      filters[i].updateIMU(gx_f, gy_f, gz_f, ax_f, ay_f, az_f);

      float roll = filters[i].getRoll();
      float pitch = filters[i].getPitch();
      float yaw = filters[i].getYaw();

      Serial.print(current_time); Serial.print("\t");
      Serial.print("MPU6050\t");
      Serial.print(locations[i]); Serial.print("\t");
      Serial.print(i); Serial.print("\t");
      Serial.print(ax); Serial.print("\t");
      Serial.print(ay); Serial.print("\t");
      Serial.print(az); Serial.print("\t");
      Serial.print(roll, 2); Serial.print("\t");
      Serial.print(pitch, 2); Serial.print("\t");
      Serial.print(yaw, 2); Serial.print("\t");
      Serial.println(0);
    }
  }
}
