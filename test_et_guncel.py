import json
import imu_guncel  # Dosya adını doğru yazdık
import time

print("="*40)
print("      IMU TEST PROGRAMI (Açı + Jiroskop)")
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


sensor = imu_guncel.ImuDevice()
print("-> Başarılı: IMU sensör nesnesi oluşturuldu.")

sensor.load_offsets(ayarlar)

print("-" * 40)
print("Kalibre edilmiş veriler okunuyor... (Durdurmak için Ctrl+C)")

try:
    while True:
        sensor.read_sensor_data()
        sensor.compute_angles()

        roll = sensor.roll
        pitch = sensor.pitch
        
        # property'yi kullanıyoruz
        pitch_rate = sensor.gyro_y_scaled

        print(f"Roll: {roll:7.2f} | Pitch: {pitch:7.2f} | Pitch Hızı: {pitch_rate:7.2f} dps", end='\r')
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\n\nProgram kullanıcı tarafından başarıyla sonlandırıldı.")
    print("="*40)
