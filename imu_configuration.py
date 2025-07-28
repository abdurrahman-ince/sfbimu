
# Görevi: ImuDevice sınıfını ve kalibrasyon fonksiyonunu modern ve kısa bir yapıda birleştirmek.

import smbus
import json
import math
import time
import os

class I2cDevice:
    def __init__(self, bus, address):
        self.bus = smbus.SMBus(bus)
        self.address = address
    def read_byte(self, register):
        return self.bus.read_byte_data(self.address, register)
    def write_byte(self, register, value):
        self.bus.write_byte_data(self.address, register, value)

class ImuDevice:
    """MPU6050 sensörünün modern ve kısa versiyonu."""
    # Sabitler
    PWR_MGMT_1, CONFIG, GYRO_CONFIG, SMPLRT_DIV = 0x6B, 0x1A, 0x1B, 0x19
    ACCEL_XOUT_H, GYRO_XOUT_H = 0x3B, 0x43
    ACCEL_SCALE, GYRO_SCALE = 16384.0, 131.0

    def __init__(self, bus=1, address=0x68):
        self.i2c = I2cDevice(bus, address)
        self.accel = {'x': 0, 'y': 0, 'z': 0}
        self.gyro = {'x': 0, 'y': 0, 'z': 0}
        self.offsets = {'accel': self.accel.copy(), 'gyro': self.gyro.copy()}
        self._roll, self._pitch = 0, 0
        
        # Sensörü Başlat
        self.i2c.write_byte(self.PWR_MGMT_1, 0x01)
        self.i2c.write_byte(self.CONFIG, 0x02)
        self.i2c.write_byte(self.GYRO_CONFIG, 0x00)
        self.i2c.write_byte(self.SMPLRT_DIV, 0x04)

    def _read_word(self, register):
        high = self.i2c.read_byte(register)
        low = self.i2c.read_byte(register + 1)
        value = (high << 8) + low
        return value - 65536 if value >= 32768 else value

    def load_offsets(self, offset_data):
        self.offsets['accel']['x'] = offset_data.get('ACCELERATION_X_OFFSET', 0)
        self.offsets['accel']['y'] = offset_data.get('ACCELERATION_Y_OFFSET', 0)
        self.offsets['accel']['z'] = offset_data.get('ACCELERATION_Z_OFFSET', 0)
        self.offsets['gyro']['x'] = offset_data.get('GYROSCOPE_X_OFFSET', 0)
        self.offsets['gyro']['y'] = offset_data.get('GYROSCOPE_Y_OFFSET', 0)
        self.offsets['gyro']['z'] = offset_data.get('GYROSCOPE_Z_OFFSET', 0)

    def read_sensor_data(self):
        accel_reg, gyro_reg = self.ACCEL_XOUT_H, self.GYRO_XOUT_H
        for axis in ['x', 'y', 'z']:
            self.accel[axis] = self._read_word(accel_reg) - self.offsets['accel'][axis]
            self.gyro[axis] = self._read_word(gyro_reg) - self.offsets['gyro'][axis]
            accel_reg += 2
            gyro_reg += 2
            
    def compute_angles(self):
        ax, ay, az = self.accel['x'], self.accel['y'], self.accel['z']
        self._roll = math.degrees(math.atan2(ay, math.sqrt(ax**2 + az**2)))
        self._pitch = math.degrees(math.atan2(-ax, math.sqrt(ay**2 + az**2)))
        
    @property
    def roll(self): return self._roll
    @property
    def pitch(self): return self._pitch

def perform_calibration(filename='setup.json'):
    os.system("clear")
    print("\n" + "="*40)
    print("      IMU KALİBRASYONU BAŞLATILIYOR")
    print("="*40)
    
    try:
        with open(filename, 'r') as f:
            setup_data = json.load(f)
        print(f"-> Mevcut '{filename}' dosyası bulundu, ayarlar korunacak.")
    except FileNotFoundError:
        print(f"-> '{filename}' bulunamadı, işlem sonunda yenisi oluşturulacak.")
        setup_data = {}

    sensor = ImuDevice()
    loop_count = 10000
    measures = {'ax': 0, 'ay': 0, 'az': 0, 'gx': 0, 'gy': 0, 'gz': 0}
    
    print(f"{loop_count} adet veri toplanıyor, lütfen bekleyin...")
    
    for i in range(loop_count):
        print("\b" + ['/', '-', '\\', '|'][i % 4], end='', flush=True)
        sensor.read_sensor_data()
        measures['ax'] += sensor.accel['x']
        measures['ay'] += sensor.accel['y']
        measures['az'] += sensor.accel['z']
        measures['gx'] += sensor.gyro['x']
        measures['gy'] += sensor.gyro['y']
        measures['gz'] += sensor.gyro['z']

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
