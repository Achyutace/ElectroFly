#include <SoftwareWire.h>

// 创建三条独立的软件I2C总线
SoftwareWire bus1(4, 5); // 第一条总线: SDA=4, SCL=5
SoftwareWire bus2(6, 7); // 第二条总线: SDA=6, SCL=7
SoftwareWire bus3(8, 9); // 第三条总线: SDA=8, SCL=9

// MPU6050 I2C地址
#define MPU6050_ADDR_68 0x68  // AD0 连接到 GND
#define MPU6050_ADDR_69 0x69  // AD0 连接到 VCC

// MPU6050寄存器地址
#define PWR_MGMT_1 0x6B
#define ACCEL_XOUT_H 0x3B
#define GYRO_XOUT_H 0x43

struct MPU6050_Data {
  int16_t accel_x, accel_y, accel_z;
  int16_t temp;
  int16_t gyro_x, gyro_y, gyro_z;
};

// 六个传感器数据存储
MPU6050_Data sensors_data[6];

// 传感器配置数组
struct SensorConfig {
  SoftwareWire* bus;
  uint8_t address;
  String name;
};

SensorConfig sensors[6] = {
  {&bus1, MPU6050_ADDR_68, "传感器1(总线1-0x68)"},
  {&bus1, MPU6050_ADDR_69, "传感器2(总线1-0x69)"},
  {&bus2, MPU6050_ADDR_68, "传感器3(总线2-0x68)"},
  {&bus2, MPU6050_ADDR_69, "传感器4(总线2-0x69)"},
  {&bus3, MPU6050_ADDR_68, "传感器5(总线3-0x68)"},
  {&bus3, MPU6050_ADDR_69, "传感器6(总线3-0x69)"}
};

void setup() {
  Serial.begin(9600);
  
  // 初始化三条I2C总线
  bus1.begin();
  bus2.begin();
  bus3.begin();
  
  Serial.println("=== 六IMU系统初始化 ===");
  Serial.println("初始化总线:");
  Serial.println("  总线1: 引脚4(SDA), 5(SCL)");
  Serial.println("  总线2: 引脚6(SDA), 7(SCL)");
  Serial.println("  总线3: 引脚8(SDA), 9(SCL)");
  Serial.println();
  
  // 初始化所有六个传感器
  int success_count = 0;
  for (int i = 0; i < 6; i++) {
    Serial.print("初始化 ");
    Serial.print(sensors[i].name);
    Serial.print("... ");
    
    if (initMPU6050(sensors[i].bus, sensors[i].address)) {
      Serial.println("成功");
      success_count++;
    } else {
      Serial.println("失败");
    }
    delay(100);
  }
  
  Serial.print("\n成功初始化 ");
  Serial.print(success_count);
  Serial.println("/6 个传感器");
  Serial.println("开始数据采集...\n");
  
  delay(1000);
}

void loop() {
  // 读取所有六个传感器的数据
  bool success[6];
  int success_count = 0;
  
  for (int i = 0; i < 6; i++) {
    success[i] = readMPU6050(sensors[i].bus, sensors[i].address, &sensors_data[i]);
    if (success[i]) success_count++;
  }
  
  // 显示读取结果
  Serial.println("============ 六传感器数据 ============");
  Serial.print("数据更新时间: ");
  Serial.print(millis());
  Serial.print("ms | 成功读取: ");
  Serial.print(success_count);
  Serial.println("/6");
  Serial.println();
  
  for (int i = 0; i < 6; i++) {
    Serial.print(sensors[i].name);
    Serial.print(" - ");
    
    if (success[i]) {
      printSensorData(&sensors_data[i]);
    } else {
      Serial.println("读取失败");
    }
  }
  
  Serial.println("=====================================");
  delay(500);
}

bool initMPU6050(SoftwareWire* wire, uint8_t address) {
  // 测试连接
  wire->beginTransmission(address);
  if (wire->endTransmission() != 0) {
    return false; // 设备未响应
  }
  
  // 唤醒MPU6050
  writeRegister(wire, address, PWR_MGMT_1, 0x00);
  delay(100);
  
  // 设置加速度计范围 (±2g)
  writeRegister(wire, address, 0x1C, 0x00);
  
  // 设置陀螺仪范围 (±250°/s)
  writeRegister(wire, address, 0x1B, 0x00);
  
  // 设置数字低通滤波器
  writeRegister(wire, address, 0x1A, 0x03);
  
  // 设置采样率分频器 (1kHz / (1 + 7) = 125Hz)
  writeRegister(wire, address, 0x19, 0x07);
  
  return true;
}

void writeRegister(SoftwareWire* wire, uint8_t deviceAddress, uint8_t registerAddress, uint8_t data) {
  wire->beginTransmission(deviceAddress);
  wire->write(registerAddress);
  wire->write(data);
  wire->endTransmission();
}

uint8_t readRegister(SoftwareWire* wire, uint8_t deviceAddress, uint8_t registerAddress) {
  wire->beginTransmission(deviceAddress);
  wire->write(registerAddress);
  wire->endTransmission(false);
  
  wire->requestFrom(deviceAddress, (uint8_t)1);
  if (wire->available()) {
    return wire->read();
  }
  return 0;
}

bool readMPU6050(SoftwareWire* wire, uint8_t address, MPU6050_Data* data) {
  uint8_t buffer[14];
  
  // 读取14个字节的传感器数据
  wire->beginTransmission(address);
  wire->write(ACCEL_XOUT_H);
  if (wire->endTransmission(false) != 0) {
    return false;
  }
  
  wire->requestFrom(address, (uint8_t)14);
  
  if (wire->available() >= 14) {
    for (int i = 0; i < 14; i++) {
      buffer[i] = wire->read();
    }
    
    // 解析数据
    data->accel_x = (buffer[0] << 8) | buffer[1];
    data->accel_y = (buffer[2] << 8) | buffer[3];
    data->accel_z = (buffer[4] << 8) | buffer[5];
    data->temp = (buffer[6] << 8) | buffer[7];
    data->gyro_x = (buffer[8] << 8) | buffer[9];
    data->gyro_y = (buffer[10] << 8) | buffer[11];
    data->gyro_z = (buffer[12] << 8) | buffer[13];
    
    return true;
  }
  
  return false;
}

void printSensorData(MPU6050_Data* data) {
  // 转换为实际物理值
  float accel_x_g = data->accel_x / 16384.0;
  float accel_y_g = data->accel_y / 16384.0;
  float accel_z_g = data->accel_z / 16384.0;
  
  float gyro_x_dps = data->gyro_x / 131.0;
  float gyro_y_dps = data->gyro_y / 131.0;
  float gyro_z_dps = data->gyro_z / 131.0;
  
  float temp_c = (data->temp / 340.0) + 36.53;
  
  Serial.print("加速度[");
  Serial.print(accel_x_g, 2);
  Serial.print(",");
  Serial.print(accel_y_g, 2);
  Serial.print(",");
  Serial.print(accel_z_g, 2);
  Serial.print("]g 陀螺仪[");
  Serial.print(gyro_x_dps, 1);
  Serial.print(",");
  Serial.print(gyro_y_dps, 1);
  Serial.print(",");
  Serial.print(gyro_z_dps, 1);
  Serial.print("]°/s 温度:");
  Serial.print(temp_c, 1);
  Serial.println("°C");
}