# 🚗 Raspberry Pi ile Şerit Takip Sistemi

Bu proje, Raspberry Pi, Picamera2 ve motor kontrolü ile çalışan basit bir **şerit takip sistemi** içerir. Görüntü işleme ile şeritler algılanır, araç yönlendirilir ve hız otomatik olarak ayarlanır.

## 📸 Proje Özeti

- OpenCV ile mor renkli şeritleri algılar.
- Hough dönüşümü ile şerit çizgilerini tespit eder.
- Araç yönünü (`DUZ`, `SOL`, `SAG`) ve dönüş açısını hesaplar.
- Raspberry Pi GPIO pinleriyle DC motorları kontrol eder.
- Canlı kamera görüntüsüne çizgiler ve bilgiler ekler.

---

## 🧰 Kullanılan Teknolojiler

- Python 3
- OpenCV
- NumPy
- RPi.GPIO
- Picamera2 (libcamera altyapısıyla)

---

## ⚙️ Donanım Gereksinimleri

- Raspberry Pi 4 (veya uyumlu model)
- Picamera2 modülü
- L298N motor sürücü
- 2 DC motor (ön ve arka tahrik)
- Mor şeritli parkur
- Harici güç kaynağı (motorlar için)

---;

Algoritmaların detaylı anlatımına sunum içerisinde ulaşabilirsiniz. 


🧠 Nasıl Çalışır?
Kamera görüntüsü HSV formatına çevrilir.

Mor renge karşılık gelen maskeyle çizgiler izole edilir.

cv.HoughLinesP ile şerit çizgileri bulunur.

Şeritlerin ortasından bir hedef nokta belirlenir.

Aracın merkezinden bu noktaya fark alınarak yön (SOL, SAG, DUZ) ve açı hesaplanır.

Motora bu yöne göre kısa süreli yön komutu verilir ve hız ayarlanır.



⚠️ Uyarılar
Araç zemini mor çizgilerle belirginleştirilmiş olmalıdır.

Motor bağlantılarını dikkatli yapın. Yanlış bağlantı kartınıza zarar verebilir.

GPIO pinleri kapatılmadan sistemi durdurmayın (CTRL+C yerine q).


Bu proje akademik öğrenim amaçlı geliştirilmiştir.
