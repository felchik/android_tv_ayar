# 📺 Android TV Ultimate Manager

Bu proje, Android TV ve Google TV cihazlarını yerel ağ üzerinden yönetmek, istenmeyen üretici uygulamalarını kaldırmak ve bilgisayardan APK yüklemek için geliştirilmiş bir PyQt6 tabanlı masaüstü aracıdır.

## ✨ Özellikler

- 🔍 Otomatik ağ taraması ile ADB portu açık cihazların tespiti
- 📋 TV’deki kurulu uygulamaların dinamik listelenmesi
- 🔎 Paket adı bazlı anlık filtreleme
- 🗑️ Seçilen uygulamaların kullanıcı bazlı kaldırılması
- 📥 Bilgisayardan APK seçip TV’ye kurma

## 🛠️ Kurulum

1. Projeyi klonlayın:
   ```bash
   git clone https://github.com/<kullanici_adiniz>/android_tv_ayar.git
   cd android_tv_ayar
   ```
2. Sanal ortam oluşturun:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. Bağımlılıkları yükleyin:
   ```bash
   pip install -r requirements.txt
   ```
4. Uygulamayı çalıştırın:
   ```bash
   python src/main.py
   ```

## 📦 Gereksinimler

- Python 3.10+
- PyQt6
- pure-python-adb

## 🔐 Not

Bu araç, ADB üzerinden çalışır. TV’nizde ADB erişimi ve cihaz ekranında izin onayı gerekir.

## 🧪 Doğrulama

Projede Python derlemesi şu komutla doğrulanabilir:

```bash
python -m py_compile src/main.py
```
