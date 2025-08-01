import smbus
import json
import math
import time
import os

# --- KalmanAngle Sınıfı ---
class KalmanAngle:
    def __init__(self):
        self.QAngle, self.QBias, self.RMeasure = 0.001, 0.003, 0.03
        self.angle, self.bias, self.rate = 0.0, 0.0, 0.0
        self.P = [[0.0, 0.0], [0.0, 0.0]]

    def getAngle(self, newAngle, newRate, dt):
        self.rate = newRate - self.bias
        self.angle += dt * self.rate
        
        self.P[0][0] += dt * (dt * self.P[1][1] - self.P[0][1] - self.P[1][0] + self.QAngle)
        self.P[0][1] -= dt * self.P[1][1]
        self.P[1][0] -= dt * self.P[1][1]
        self.P[1][1] += self.QBias * dt

        y = newAngle - self.angle
        s = self.P[0][0] + self.RMeasure
        K = [self.P[0][0] / s, self.P[1][0] / s]

        self.angle += K[0] * y
        self.bias  += K[1] * y

        P00Temp, P01Temp = self.P[0][0], self.P[0][1] # Tek satırda atama
        self.P[0][0] -= K[0] * P00Temp
        self.P[0][1] -= K[0] * P01Temp
        self.P[1][0] -= K[1] * P00Temp
        self.P[1][1] -= K[1] * P01Temp
        return self.angle

    def setAngle(self, angle): self.angle = angle
    def setQAngle(self, QAngle): self.QAngle = QAngle
    def setQBias(self, QBias): self.QBias = QBias
    def setRMeasure(self, RMeasure): self.RMeasure = RMeasure
    def getRate(self): return self.rate
    def getQAngle(self): return self.QAngle
    def getQBias(self): return self.QBias
    def getRMeasure(self): return self.RMeasure
# --- KalmanAngle Sınıfı Sonu ---


class I2cDevice:
    def __init__(self, bus, address):
        self.bus, self.address = smbus.SMBus(bus), address # Tek satırda atama
    def read_byte(self, register): return self.bus.read_byte_data(self.address, register)
    def write_byte(self, register, value): self.bus.write_byte_data(self.address, register, value)


class ImuDevice:
    """MPU6050 sensörünün modern ve kısa versiyonu."""
    PWR_MGMT_1, CONFIG, GYRO_CONFIG, SMPLRT_DIV = 0x6B, 0x1A, 0x1B, 0x19
    ACCEL_XOUT_H, GYRO_XOUT_H = 0x3B, 0x43
    ACCEL_SCALE, GYRO_SCALE = 16384.0, 131.0

    def __init__(self, bus=1, address=0x68):
        self.i2c = I2cDevice(bus, address)
        self.accel, self.gyro = {'x': 0, 'y': 0, 'z': 0}, {'x': 0, 'y': 0, 'z': 0}
        self.offsets = {'accel': self.accel.copy(), 'gyro': self.gyro.copy()}
        
        self._roll, self._pitch = 0, 0
        self._last_time = time.time()

        self.kalmanX, self.kalmanY = KalmanAngle(), KalmanAngle() # Tek satırda oluşturma
        
        # Sensörü Başlat (Tek satırda toplama)
        self.i2c.write_byte(self.PWR_MGMT_1, 0x01)
        self.i2c.write_byte(self.CONFIG, 0x02)
        self.i2c.write_byte(self.GYRO_CONFIG, 0x00)
        self.i2c.write_byte(self.SMPLRT_DIV, 0x04)

        # İlk Kalman Filtresi Başlatma
        self.read_sensor_data()
        ax_g_init, ay_g_init, az_g_init = self.accel['x'] / self.ACCEL_SCALE, \
                                          self.accel['y'] / self.ACCEL_SCALE, \
                                          self.accel['z'] / self.ACCEL_SCALE

        initial_roll_acc, initial_pitch_acc = 0.0, 0.0
        if az_g_init != 0: initial_roll_acc = math.degrees(math.atan2(ay_g_init, az_g_init))
        
        denominator_pitch = math.sqrt(ay_g_init**2 + az_g_init**2) 
        if denominator_pitch != 0: initial_pitch_acc = math.degrees(math.atan2(-ax_g_init, denominator_pitch))
        
        self.kalmanX.setAngle(initial_roll_acc)
        self.kalmanY.setAngle(initial_pitch_acc)


    def _read_word(self, register):
        high, low = self.i2c.read_byte(register), self.i2c.read_byte(register + 1) # Tek satırda okuma
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
            accel_reg, gyro_reg = accel_reg + 2, gyro_reg + 2 # Tek satırda artırma
            
    def compute_angles(self):
        self.read_sensor_data()

        current_time = time.time()
        dt = current_time - self._last_time
        self._last_time = current_time

        ax_g, ay_g, az_g = self.accel['x'] / self.ACCEL_SCALE, \
                           self.accel['y'] / self.ACCEL_SCALE, \
                           self.accel['z'] / self.ACCEL_SCALE

        gx_dps, gy_dps = self.gyro['x'] / self.GYRO_SCALE, \
                         self.gyro['y'] / self.GYRO_SCALE

        roll_acc, pitch_acc = 0.0, 0.0
        if az_g != 0: roll_acc = math.degrees(math.atan2(ay_g, az_g))
        else: roll_acc = self._roll

        denominator_pitch = math.sqrt(ay_g**2 + az_g**2) 
        if denominator_pitch != 0: pitch_acc = math.degrees(math.atan2(-ax_g, denominator_pitch))
        else: pitch_acc = self._pitch
            
        self._roll = self.kalmanX.getAngle(roll_acc, gx_dps, dt)
        self._pitch = self.kalmanY.getAngle(pitch_acc, gy_dps, dt)
        
    @property
    def roll(self): return self._roll
    
    @property
    def pitch(self): return self._pitch

    @staticmethod
    def perform_calibration(filename='setup.json'):
        os.system("clear")
        print("\n" + "="*40)
        print("      IMU KALİBRASYONU BAŞLATILIYOR")
        print("="*40)
        
        try:
            with open(filename, 'r') as f: setup_data = json.load(f)
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
            
            original_accel_offsets, original_gyro_offsets = sensor.offsets['accel'].copy(), sensor.offsets['gyro'].copy() # Tek satırda kopyalama
            sensor.offsets = {'accel': {'x': 0, 'y': 0, 'z': 0}, 'gyro': {'x': 0, 'y': 0, 'z': 0}}
            sensor.read_sensor_data()

            measures['ax'] += sensor.accel['x']
            measures['ay'] += sensor.accel['y']
            measures['az'] += sensor.accel['z']
            measures['gx'] += sensor.gyro['x']
            measures['gy'] += sensor.gyro['y']
            measures['gz'] += sensor.gyro['z']
            
            sensor.offsets['accel'], sensor.offsets['gyro'] = original_accel_offsets, original_gyro_offsets # Tek satırda geri yükleme

        print("\n\nVeri toplama tamamlandı. Ofsetler hesaplanıyor...")

        setup_data['ACCELERATION_X_OFFSET'] = int(measures['ax'] / loop_count)
        setup_data['ACCELERATION_Y_OFFSET'] = int(measures['ay'] / loop_count)
        setup_data['ACCELERATION_Z_OFFSET'] = int(measures['az'] / loop_count) - 16384
        setup_data['GYROSCOPE_X_OFFSET'] = int(measures['gx'] / loop_count)
        setup_data['GYROSCOPE_Y_OFFSET'] = int(measures['gy'] / loop_count)
        setup_data['GYROSCOPE_Z_OFFSET'] = int(measures['gz'] / loop_count)
        
        with open(filename, "w") as f: json.dump(setup_data, f, indent=4) # Tek satırda yazma
            
        print(f"-> Başarılı: Ofsetler '{filename}' dosyasına kaydedildi.")
        print("="*40 + "\n")

    def read_json(self, config_file):
        """Kalibrasyon ayarlarını JSON dosyasından yükler."""
        print("="*40)
        print("      MODERN IMU TEST PROGRAMI")
        print("="*40)

        try:
            with open(config_file, 'r') as f: ayarlar = json.load(f) # Tek satırda yükleme
            print(f"-> Başarılı: '{config_file}' kalibrasyon dosyası bulundu.")
        except FileNotFoundError:
            print(f"\n!!! UYARI: '{config_file}' dosyası bulunamadı!")
            print(f"!!! Çözüm: Lütfen önce bu dosyayı ('{os.path.basename(__file__)}') doğrudan çalıştırarak kalibrasyon yapın.\n")
            exit()
        return ayarlar

if __name__ == '__main__':
    print("Bu dosya bir modül (alet kutusu) olarak tasarlanmıştır.")
    print("Doğrudan çalıştırıldığında, sadece kalibrasyon işlemi yapacaktır.")
    input("Lütfen sensörün düz bir zeminde olduğundan emin olun ve devam etmek için Enter'a basın...")
    ImuDevice.perform_calibration()
