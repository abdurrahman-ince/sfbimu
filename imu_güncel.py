import i2c

import math

import time



class ImuDevice:

    # Sabitleri sınıf seviyesinde tanımlamak daha düzenlidir.

    PWR_MGMT_1 = 0x6B

    CONFIG = 0x1A

    GYRO_CONFIG = 0x1B # Orijinal kodda yanlışlıkla 0x18 yazılmış, datasheet'e göre 0x1B olmalı.

    SMPLRT_DIV = 0x19

    ACCEL_XOUT_H = 0x3B

    GYRO_XOUT_H = 0x43

    

    ACCEL_SCALE = 16384.0

    GYRO_SCALE = 131.0



    def __init__(self, bus=1, address=0x68):

        self.i2c = i2c.I2cDevice(bus, address)

        

        # Değerleri ve ofsetleri sözlüklerde (dictionary) tutuyoruz.

        self.accel = {'x': 0, 'y': 0, 'z': 0}

        self.gyro = {'x': 0, 'y': 0, 'z': 0}

        self.offsets = {

            'accel': {'x': 0, 'y': 0, 'z': 0},

            'gyro': {'x': 0, 'y': 0, 'z': 0}

        }

        

        self._roll = 0

        self._pitch = 0

        

        # Sensörü uyandır ve ayarla

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

        """JSON'dan okunan tüm ofsetleri tek seferde yükler."""

        self.offsets['accel']['x'] = offset_data.get('ACCELERATION_X_OFFSET', 0)

        self.offsets['accel']['y'] = offset_data.get('ACCELERATION_Y_OFFSET', 0)

        self.offsets['accel']['z'] = offset_data.get('ACCELERATION_Z_OFFSET', 0)

        self.offsets['gyro']['x'] = offset_data.get('GYROSCOPE_X_OFFSET', 0)

        self.offsets['gyro']['y'] = offset_data.get('GYROSCOPE_Y_OFFSET', 0)

        self.offsets['gyro']['z'] = offset_data.get('GYROSCOPE_Z_OFFSET', 0)

        print("-> IMU ofsetleri başarıyla yüklendi.")



    def read_sensor_data(self):

        """Tüm sensör verilerini tek bir fonksiyonda okur ve ofsetleri uygular."""

        base_reg_accel = self.ACCEL_XOUT_H

        base_reg_gyro = self.GYRO_XOUT_H

        

        for axis in ['x', 'y', 'z']:

            self.accel[axis] = self._read_word(base_reg_accel) - self.offsets['accel'][axis]

            self.gyro[axis] = self._read_word(base_reg_gyro) - self.offsets['gyro'][axis]

            base_reg_accel += 2

            base_reg_gyro += 2

            

    def compute_angles(self):

        """Okunan verilere göre roll ve pitch açılarını hesaplar."""

        ax, ay, az = self.accel['x'], self.accel['y'], self.accel['z']

        self._roll = math.degrees(math.atan2(ay, math.sqrt(ax**2 + az**2)))

        self._pitch = math.degrees(math.atan2(-ax, math.sqrt(ay**2 + az**2)))

        

    # @property sayesinde bu metodlara sensor.roll gibi değişken gibi erişilebilir.

    @property

    def roll(self):

        return self._roll



    @property

    def pitch(self):

        return self._pitch



    # Örnek olarak scaled (ölçeklenmiş) değerler için de property'ler

    @property

    def accel_x_scaled(self):

        return self.accel['x'] / self.ACCEL_SCALE

        

    @property

    def gyro_x_scaled(self):

        return self.gyro['x'] / self.GYRO_SCALE
