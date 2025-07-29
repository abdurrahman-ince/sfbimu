import json
import time
import os
import imu_kalman # Kalman filtreli IMU kodunuzu import ediyoruz

print("="*40)
print("      CANLI KALMAN FİLTRELİ IMU TESTİ")
print("="*40)

config_file = 'setup.json'

try:
    # ImuDevice nesnesi oluştur (bu sensörü başlatacak ve Kalman'ı init edecek)
    # imu_kalman modülünün içindeki ImuDevice sınıfını kullanıyoruz
    imu = imu_kalman.ImuDevice() 
    print("-> Başarılı: IMU sensör nesnesi oluşturuldu.")

    # Kalibrasyon ayarlarını yükle
    # ImuDevice nesnesi üzerinden read_json metodunu çağırıyoruz
    ayarlar = imu.read_json(config_file) 
    imu.load_offsets(ayarlar)
    print(f"-> Başarılı: '{config_file}' kalibrasyon dosyası yüklendi.")

except FileNotFoundError:
    print(f"\n!!! UYARI: '{config_file}' dosyası bulunamadı!")
    # os.path.basename(__file__) ile imu_kalman.py dosyasının adını dinamik olarak alıyoruz
    print(f"!!! Çözüm: Lütfen önce '{os.path.basename(imu_kalman.__file__)}' dosyasını doğrudan çalıştırarak kalibrasyon yapın.\n")
    exit()
except Exception as e:
    print(f"Bir hata oluştu: {e}")
    exit()

print("-" * 40)
print("Canlı Kalman Filtreli veriler okunuyor... (Durdurmak için Ctrl+C)")
print("-" * 40)

try:
    while True:
        # Sensörden veri oku, filtrele ve açıları güncelle
        imu.compute_angles()

        # Filtrelenmiş verilere eriş
        filtered_roll = imu.roll
        filtered_pitch = imu.pitch

        # Canlı veriyi aynı satırda güncelleyerek yazdır
        print(f"Filtrelenmiş Roll: {filtered_roll:7.2f} derece   |   Filtrelenmiş Pitch: {filtered_pitch:7.2f} derece", end='\r', flush=True)
        
        # Daha hızlı ve gerçek zamanlı bir gözlem için örnekleme hızı (100 Hz)
        time.sleep(0.01) 

except KeyboardInterrupt:
    print("\n\nProgram kullanıcı tarafından başarıyla sonlandırıldı.")
except Exception as e:
    print(f"\nBeklenmeyen bir hata oluştu: {e}")
