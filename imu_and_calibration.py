# Bu dosyanın adı: imu_ve_kalibrasyon_araci.py (Düzeltilmiş Hali)
# Görevi: ImuDevice sınıfını ve kalibrasyon fonksiyonunu tek bir modülde birleştirmek.

import smbus
import json
import math
import time
import os

class I2cDevice:
    """I2C iletişimini basitleştiren aracı sınıf."""
    def __init__(self, bus, address):
        self.bus = smbus.SMBus(bus)
        self.address = address

    def read_byte(self, register):
        return self.bus.read_byte_data(self.address, register)

    def write_byte(self, register, value):
        self.bus.write_byte_data(self.address, register, value)

class ImuDevice:
    """MPU6050 sensörünü temsil eden ve onunla konuşan ana sınıf."""
    IMU_BUS = 1
    IMU_ADDRESS = 0x68
    PWR_MGMT_1 = 0x6B
    GYRO_CONFIG = 0x18
    SMPLRT_DIV = 0x19
    CONFIG = 0x1A
    ACCEL_XOUT_H = 0x3B
    ACCEL_YOUT_H = 0x3D
    ACCEL_ZOUT_H = 0x3F
    GYRO_XOUT_H = 0x43
    GYRO_YOUT_H = 0x45
    GYRO_ZOUT_H = 0x47
    XA_OFFSET_H = 0x06
    YA_OFFSET_H = 0x08
    ZA_OFFSET_H = 0x0A
    XG_OFFSET_H = 0x13
    YG_OFFSET_H = 0x15
    ZG_OFFSET_H = 0x17
    ACCELERATION_SCALE_FACTOR = 16384.0
    GYROSCOPE_SCALE_FACTOR = 131.0

    def __init__(self):
        self.i2c_device = I2cDevice(self.IMU_BUS, self.IMU_ADDRESS)
        self.acceleration_x, self.acceleration_y, self.acceleration_z = 0, 0, 0
        self.gyroscope_x, self.gyroscope_y, self.gyroscope_z = 0, 0, 0
        self.acceleration_offset_x, self.acceleration_offset_y, self.acceleration_offset_z = 0, 0, 0
        self.gyroscope_offset_x, self.gyroscope_offset_y, self.gyroscope_offset_z = 0, 0, 0
        self.roll, self.pitch = 0, 0
        self.roll_rate, self.pitch_rate, self.yaw_rate = 0, 0, 0
        self.i2c_device.write_byte(self.PWR_MGMT_1, 0x01)
        self.i2c_device.write_byte(self.CONFIG, 0x02)
        self.i2c_device.write_byte(self.GYRO_CONFIG, 0x00)
        self.i2c_device.write_byte(self.SMPLRT_DIV, 0x04)

    def __read_word__(self, register):
        higher_byte = self.i2c_device.read_byte(register)
        lower_byte = self.i2c_device.read_byte(register + 1)
        value = (higher_byte << 8) + lower_byte
        if value > 32768:
            value = value - 65536
        return value

    def __write_word__(self, register, value):
        self.i2c_device.write_byte(register, value >> 8)
        self.i2c_device.write_byte(register + 1, value & 0x00FF)

    def reset_offsets(self):
        self.acceleration_offset_x, self.acceleration_offset_y, self.acceleration_offset_z = 0, 0, 0
        self.gyroscope_offset_x, self.gyroscope_offset_y, self.gyroscope_offset_z = 0, 0, 0

    def read_acceleration_data(self):
        self.acceleration_x = self.__read_word__(self.ACCEL_XOUT_H) - self.acceleration_offset_x
        self.acceleration_y = self.__read_word__(self.ACCEL_YOUT_H) - self.acceleration_offset_y
        self.acceleration_z = self.__read_word__(self.ACCEL_ZOUT_H) - self.acceleration_offset_z

    def read_gyroscope_data(self):
        self.gyroscope_x = self.__read_word__(self.GYRO_XOUT_H) - self.gyroscope_offset_x
        self.gyroscope_y = self.__read_word__(self.GYRO_YOUT_H) - self.gyroscope_offset_y
        self.gyroscope_z = self.__read_word__(self.GYRO_ZOUT_H) - self.gyroscope_offset_z

    def get_x_acceleration(self): return self.acceleration_x
    def get_y_acceleration(self): return self.acceleration_y
    def get_z_acceleration(self): return self.acceleration_z
    def get_x_gyroscope(self): return self.gyroscope_x
    def get_y_gyroscope(self): return self.gyroscope_y
    def get_z_gyroscope(self): return self.gyroscope_z
    def get_roll(self): return self.roll
    def get_pitch(self): return self.pitch
    def set_x_acceleration_offset(self, offset): self.acceleration_offset_x = offset
    def set_y_acceleration_offset(self, offset): self.acceleration_offset_y = offset
    def set_z_acceleration_offset(self, offset): self.acceleration_offset_z = offset
    def set_x_gyroscope_offset(self, offset): self.gyroscope_offset_x = offset
    def set_y_gyroscope_offset(self, offset): self.gyroscope_offset_y = offset
    def set_z_gyroscope_offset(self, offset): self.gyroscope_offset_z = offset

    def compute_angles(self):
        self.roll = math.degrees(math.atan2(self.acceleration_y, math.sqrt(self.acceleration_x**2 + self.acceleration_z**2)))
        self.pitch = math.degrees(math.atan2(-self.acceleration_x, math.sqrt(self.acceleration_y**2 + self.acceleration_z**2)))

def perform_calibration(filename='setup.json'):
    os.system("clear")
    print("\n" + "="*40)
    print("      IMU KALİBRASYONU BAŞLATILIYOR")
    print("="*40)

    try:
        with open(filename, 'r') as json_file:
            setup_data = json.load(json_file)
        print(f"-> Mevcut '{filename}' dosyası bulundu, ayarlar korunacak.")
    except FileNotFoundError:
        print(f"-> '{filename}' bulunamadı, işlem sonunda yenisi oluşturulacak.")
        setup_data = {}

    # --- HATA BURADAYDI ---
    # imu.ImuDevice() yerine doğrudan ImuDevice() olarak çağırıyoruz
    imu_device = ImuDevice()
    # --- DÜZELTME SONU ---
    
    imu_device.reset_offsets()

    loop_count = 10000
    measures = {'ax': 0, 'ay': 0, 'az': 0, 'gx': 0, 'gy': 0, 'gz': 0}

    print(f"{loop_count} adet veri toplanıyor, lütfen bekleyin...")

    for i in range(loop_count):
        print("\b" + ['/', '-', '\\', '|'][i % 4], end='', flush=True)
        imu_device.read_acceleration_data()
        imu_device.read_gyroscope_data()
        measures['ax'] += imu_device.get_x_acceleration()
        measures['ay'] += imu_device.get_y_acceleration()
        measures['az'] += imu_device.get_z_acceleration()
        measures['gx'] += imu_device.get_x_gyroscope()
        measures['gy'] += imu_device.get_y_gyroscope()
        measures['gz'] += imu_device.get_z_gyroscope()

    print("\n\nVeri toplama tamamlandı. Ofsetler hesaplanıyor...")

    setup_data['ACCELERATION_X_OFFSET'] = int(measures['ax'] / loop_count)
    setup_data['ACCELERATION_Y_OFFSET'] = int(measures['ay'] / loop_count)
    setup_data['ACCELERATION_Z_OFFSET'] = int(measures['az'] / loop_count) - 16384
    setup_data['GYROSCOPE_X_OFFSET'] = int(measures['gx'] / loop_count)
    setup_data['GYROSCOPE_Y_OFFSET'] = int(measures['gy'] / loop_count)
    setup_data['GYROSCOPE_Z_OFFSET'] = int(measures['gz'] / loop_count)

    with open(filename, "w") as f:
        json.dump(setup_data, f, indent=4)

    print(f"-> Başarılı: Ofsetler '{filename}' dosyasına kaydedildi.")
    print("="*40 + "\n")

if __name__ == '__main__':
    print("Bu dosya bir modül (alet kutusu) olarak tasarlanmıştır.")
    print("Doğrudan çalıştırıldığında, sadece kalibrasyon işlemi yapacaktır.")
    input("Lütfen sensörün düz bir zeminde olduğundan emin olun ve devam etmek için Enter'a basın...")
    perform_calibration()
