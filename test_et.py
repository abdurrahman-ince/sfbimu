import json
import imu
import time

print("="*40)
print("      IMU TEST VE VERİ OKUMA PROGRAMI")
print("="*40)
print("Ana test programı başlatıldı.")

try:
    with open('setup.json', 'r') as f:
        ayarlar = json.load(f)
    print("-> Başarılı: 'setup.json' kalibrasyon dosyası okundu.")
except FileNotFoundError:
    print("\n!!! HATA: 'setup.json' dosyası bulunamadı!")
    print("!!! Çözüm: Lütfen önce 'calibrate.py' programını çalıştırın.\n")
    exit()
except json.JSONDecodeError:
    print("\n!!! HATA: 'setup.json' dosyası okunamadı veya formatı bozuk!")
    print("!!! Çözüm: 'setup.json' dosyasını silip 'calibrate.py' programını tekrar çalıştırın.\n")
    exit()

sensor = imu.ImuDevice()
print("-> Başarılı: IMU sensör nesnesi oluşturuldu (ofsetler şu an '0').")

try:
    sensor.set_x_acceleration_offset(ayarlar['ACCELERATION_X_OFFSET'])
    sensor.set_y_acceleration_offset(ayarlar['ACCELERATION_Y_OFFSET'])
    sensor.set_z_acceleration_offset(ayarlar['ACCELERATION_Z_OFFSET'])
    sensor.set_x_gyroscope_offset(ayarlar['GYROSCOPE_X_OFFSET'])
    sensor.set_y_gyroscope_offset(ayarlar['GYROSCOPE_Y_OFFSET'])
    sensor.set_z_gyroscope_offset(ayarlar['GYROSCOPE_Z_OFFSET'])
    print("-> Başarılı: Ofset değerleri sensör nesnesine yüklendi.")
except KeyError as e:
    print(f"\n!!! HATA: 'setup.json' dosyasında eksik bir anahtar var: {e}")
    print("!!! Çözüm: 'setup.json' dosyasını silip 'calibrate.py' programını tekrar çalıştırın.\n")
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
    print("="*40)
