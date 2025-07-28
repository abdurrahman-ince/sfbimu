# Bu dosyanın adı: test_et.py
# Görevi: imu_and_calibration.py modülünü kullanarak sensörden veri okumak.

import json
import time
# --- DEĞİŞİKLİK: Artık yeni dosya adımızı import ediyoruz ---
import imu_and_calibration

print("="*40)
print("      IMU TEST VE VERİ OKUMA PROGRAMI")
print("="*40)

config_file = 'setup.json'

# Önce kalibrasyon dosyasının varlığını kontrol et
try:
    with open(config_file, 'r') as f:
        ayarlar = json.load(f)
    print(f"-> Başarılı: '{config_file}' kalibrasyon dosyası bulundu.")
except FileNotFoundError:
    print(f"\n!!! UYARI: '{config_file}' dosyası bulunamadı.")
    print(f"!!! Lütfen önce 'imu_and_calibration.py' dosyasını çalıştırarak kalibrasyon yapın.")
    exit()

# --- DEĞİŞİKLİK: Nesneyi doğru modülden (yeni dosya adıyla) oluşturuyoruz ---
sensor = imu_and_calibration.ImuDevice()
print("-> Başarılı: IMU sensör nesnesi oluşturuldu.")

# Ofsetleri sensör nesnesine yükle
try:
    sensor.set_x_acceleration_offset(ayarlar['ACCELERATION_X_OFFSET'])
    sensor.set_y_acceleration_offset(ayarlar['ACCELERATION_Y_OFFSET'])
    sensor.set_z_acceleration_offset(ayarlar['ACCELERATION_Z_OFFSET'])
    sensor.set_x_gyroscope_offset(ayarlar['GYROSCOPE_X_OFFSET'])
    sensor.set_y_gyroscope_offset(ayarlar['GYROSCOPE_Y_OFFSET'])
    sensor.set_z_gyroscope_offset(ayarlar['GYROSCOPE_Z_OFFSET'])
    print("-> Başarılı: Ofset değerleri sensör nesnesine yüklendi.")
except KeyError as e:
    print(f"\n!!! HATA: '{config_file}' dosyasında eksik anahtar var: {e}")
    print(f"!!! Çözüm: Lütfen 'imu_and_calibration.py' dosyasını çalıştırarak kalibrasyonu yenileyin.")
    exit()

print("-" * 40)
print("Kalibre edilmiş veriler okunuyor... (Durdurmak için Ctrl+C)")

try:
    while True:
        sensor.read_acceleration_data()
        sensor.read_gyroscope_data()
        sensor.compute_angles()

        roll = sensor.get_roll()
        pitch = sensor.get_pitch()

        print(f"Roll Açısı: {roll:7.2f} derece   |   Pitch Açısı: {pitch:7.2f} derece", end='\r')
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\n\nProgram kullanıcı tarafından başarıyla sonlandırıldı.")
