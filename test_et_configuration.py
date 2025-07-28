
# Görevi: imu_configuration.py modülünü kullanarak sensörden veri okumak.

import json
import time
import imu_configuration

print("="*40)
print("      MODERN IMU TEST PROGRAMI")
print("="*40)

config_file = 'setup.json'

try:
    with open(config_file, 'r') as f:
        ayarlar = json.load(f)
    print(f"-> Başarılı: '{config_file}' kalibrasyon dosyası bulundu.")
except FileNotFoundError:
    print(f"\n!!! UYARI: '{config_file}' dosyası bulunamadı!")
    # --- GÜNCELLEME: Hata mesajındaki dosya adını da güncelliyoruz ---
    print(f"!!! Çözüm: Lütfen önce 'imu_configuration.py' dosyasını çalıştırarak kalibrasyon yapın.\n")
    exit()

# --- GÜNCELLEME: Nesneyi doğru modülden (yeni dosya adıyla) oluşturuyoruz ---
sensor = imu_configuration.ImuDevice()
print("-> Başarılı: IMU sensör nesnesi oluşturuldu.")

# Tek bir komutla ofsetleri yüklüyoruz
sensor.load_offsets(ayarlar)

print("-" * 40)
print("Kalibre edilmiş veriler okunuyor... (Durdurmak için Ctrl+C)")

try:
    while True:
        sensor.read_sensor_data()
        sensor.compute_angles()

        # @property sayesinde verilere daha temiz erişiyoruz
        roll = sensor.roll
        pitch = sensor.pitch

        print(f"Roll Açısı: {roll:7.2f} derece   |   Pitch Açısı: {pitch:7.2f} derece", end='\r')
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\n\nProgram kullanıcı tarafından başarıyla sonlandırıldı.")
