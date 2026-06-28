import sys
import os
import socket
import threading
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLineEdit, QPushButton, QTextEdit, 
                             QLabel, QListWidget, QListWidgetItem, QMessageBox, 
                             QComboBox, QFileDialog)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from ppadb.client import Client as AdbClient

# Arka plan işlemlerinde (Tarama/Yükleme) arayüzün donmasını engelleyen sinyal mekanizması
class ScannerSignals(QObject):
    device_found = pyqtSignal(str)
    scan_finished = pyqtSignal()
    apps_loaded = pyqtSignal(list)

class TVManagerUltimate(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Android TV - Gelişmiş Yönetim Paneli (Next ve Tüm TV'ler)")
        self.setGeometry(100, 100, 600, 750)
        
        self.signals = ScannerSignals()
        self.signals.device_found.connect(self.on_device_found)
        self.signals.scan_finished.connect(self.on_scan_finished)
        self.signals.apps_loaded.connect(self.on_apps_loaded)
        
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # --- 1. BÖLÜM: Otomatik Ağ Tarama ---
        scan_layout = QHBoxLayout()
        self.btn_scan = QPushButton("Ağdaki TV'leri Tara")
        self.btn_scan.clicked.connect(self.start_network_scan)
        self.btn_scan.setStyleSheet("background-color: #0275d8; color: white; font-weight: bold; padding: 6px;")
        
        self.combo_devices = QComboBox()
        self.combo_devices.setEditable(True)
        self.combo_devices.setPlaceholderText("TV IP Adresi Seçin veya Yazın")
        self.combo_devices.currentTextChanged.connect(self.on_combo_changed)
        
        scan_layout.addWidget(self.btn_scan)
        scan_layout.addWidget(self.combo_devices)
        main_layout.addLayout(scan_layout)
        
        # --- 2. BÖLÜM: Bağlantı ---
        ip_layout = QHBoxLayout()
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("IP Adresi ve Port (Örn: 192.168.1.108:40269 veya 192.168.1.108)")
        
        self.btn_connect = QPushButton("TV'ye Bağlan ve Bilgileri Çek")
        self.btn_connect.clicked.connect(self.connect_to_tv)
        self.btn_connect.setStyleSheet("background-color: #5cb85c; color: white; font-weight: bold; padding: 6px;")
        
        ip_layout.addWidget(self.ip_input)
        ip_layout.addWidget(self.btn_connect)
        main_layout.addLayout(ip_layout)
        
        # --- 3. BÖLÜM: Arama / Filtreleme Çubuğu ---
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Uygulama Ara / Filtrele:"))
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Örn: next, amazon, analytics, tv...")
        self.filter_input.textChanged.connect(self.filter_apps)
        filter_layout.addWidget(self.filter_input)
        main_layout.addLayout(filter_layout)
        
        # --- 4. BÖLÜM: Dinamik Uygulama Listesi ---
        main_layout.addWidget(QLabel("TV'de Yüklü Uygulamalar (İşlem yapmak için seçin):"))
        self.list_widget = QListWidget()
        main_layout.addWidget(self.list_widget)
        
        # --- 5. BÖLÜM: Aksiyon Butonları ---
        buttons_layout = QHBoxLayout()
        
        self.btn_delete = QPushButton("Seçilenleri TV'den Kaldır")
        self.btn_delete.setStyleSheet("background-color: #d9534f; color: white; font-weight: bold; padding: 10px;")
        self.btn_delete.clicked.connect(self.delete_selected_apps)
        self.btn_delete.setEnabled(False)
        
        self.btn_install_apk = QPushButton("Bilgisayardan APK Yükle")
        self.btn_install_apk.setStyleSheet("background-color: #f0ad4e; color: white; font-weight: bold; padding: 10px;")
        self.btn_install_apk.clicked.connect(self.choose_and_install_apk)
        self.btn_install_apk.setEnabled(False)
        
        buttons_layout.addWidget(self.btn_delete)
        buttons_layout.addWidget(self.btn_install_apk)
        main_layout.addLayout(buttons_layout)
        
        # --- 6. BÖLÜM: İşlem Günlüğü (Log) ---
        main_layout.addWidget(QLabel("Sistem Günlüğü:"))
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(150)
        main_layout.addWidget(self.log_output)
        
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def log(self, text):
        self.log_output.append(text)

    def on_combo_changed(self, text):
        self.ip_input.setText(text)

    # --- 🔍 Otomatik Ağ Tarama Mantığı ---
    def start_network_scan(self):
        self.btn_scan.setEnabled(False)
        self.btn_scan.setText("Aranıyor...")
        self.combo_devices.clear()
        self.log("\nYerel ağ taranıyor, cihazlar aranıyor...")
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            self.subnet = ".".join(local_ip.split(".")[:3]) + "."
        except Exception:
            self.subnet = "192.168.1."
        threading.Thread(target=self.scan_network_thread, daemon=True).start()

    def scan_network_thread(self):
        threads = []
        for i in range(1, 255):
            t = threading.Thread(target=self.check_adb_port, args=(self.subnet + str(i),))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        self.signals.scan_finished.emit()

    def check_adb_port(self, ip):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.2)
            # Hem klasik 5555 portunu hem de diğer standart portları tarayabiliriz, şimdilik 5555 varsayılan
            if sock.connect_ex((ip, 5555)) == 0:
                self.signals.device_found.emit(ip)
            sock.close()
        except Exception: pass

    def on_device_found(self, ip):
        self.combo_devices.addItem(ip)
        self.ip_input.setText(ip)

    def on_scan_finished(self):
        self.btn_scan.setEnabled(True)
        self.btn_scan.setText("Ağdaki TV'leri Tara")
        self.log(f"Tarama tamamlandı. {self.combo_devices.count()} adet cihaz otomatik listede.")

    # --- 🔌 TV Bağlantısı ve Uygulama Çekme ---
    def connect_to_tv(self):
        ip = self.ip_input.text().strip()
        if not ip:
            QMessageBox.warning(self, "Eksik Bilgi", "Lütfen bir IP adresi girin veya yukarıdan taratın.")
            return
        
        self.log(f"\n{ip} adresine ADB protokolü ile bağlanılıyor...")
        try:
            os.system("adb start-server")
            self.adb_client = AdbClient(host="127.0.0.1", port=5037)
            
            # Eğer kullanıcı portu elle yazdıysa (Örn: 192.168.1.108:40269)
            if ":" in ip:
                self.device = self.adb_client.device(ip)
            else:
                # Yazmadıysa varsayılan 5555 portuyla bağlanmayı dener
                self.adb_client.remote_connect(ip, 5555)
                self.device = self.adb_client.device(f"{ip}:5555")
            
            if self.device:
                self.log("BAĞLANTI BAŞARILI! TV ile eşleşme sağlandı.")
                self.log("Uygulama listesi TV'den çekiliyor, lütfen arayüz gelene kadar bekleyin...")
                threading.Thread(target=self.fetch_tv_apps, daemon=True).start()
            else:
                self.log("Cihaz bağlandı ancak komutları reddediyor. TV ekranındaki ADB İZİN penceresini onaylayın.")
        except Exception as e:
            self.log(f"Bağlantı Başarısız: {str(e)}")

    def fetch_tv_apps(self):
        try:
            raw_apps = self.device.shell("pm list packages")
            lines = raw_apps.splitlines()
            clean_packages = []
            for line in lines:
                if line.startswith("package:"):
                    clean_packages.append(line.replace("package:", "").strip())
            clean_packages.sort()
            self.signals.apps_loaded.emit(clean_packages)
        except Exception as e:
            print(f"Hata: {e}")

    def on_apps_loaded(self, apps):
        self.list_widget.clear()
        for pkg in apps:
            item = QListWidgetItem(pkg)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, pkg)
            self.list_widget.addItem(item)
            
        self.log(f"Başarılı: TV'de bulunan {len(apps)} uygulama dinamik olarak yüklendi.")
        self.btn_delete.setEnabled(True)
        self.btn_install_apk.setEnabled(True)

    # --- 🔍 Canlı Filtreleme ---
    def filter_apps(self, text):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    # --- 🗑️ Uygulama Silme Bölümü ---
    def delete_selected_apps(self):
        selected_packages = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_packages.append(item.data(Qt.ItemDataRole.UserRole))

        if not selected_packages:
            QMessageBox.warning(self, "Seçim Yok", "Lütfen silinmesini istediğiniz uygulamaların yanındaki kutucukları işaretleyin.")
            return

        onay = QMessageBox.question(self, "Onay", f"Seçilen {len(selected_packages)} uygulamayı TV'den kaldırmak istediğinize emin misiniz?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if onay == QMessageBox.StandardButton.No:
            return

        self.log("\n--- Kaldırma İşlemi Başlatıldı ---")
        for pkg in selected_packages:
            self.log(f"{pkg} kaldırılıyor...")
            try:
                result = self.device.shell(f"pm uninstall -k --user 0 {pkg}")
                if "Success" in result:
                    self.log(f"-> SİLİNDİ: {pkg}")
                else:
                    self.log(f"-> BAŞARISIZ: {pkg} ({result.strip()})")
            except Exception as e:
                self.log(f"-> HATA: {str(e)}")
        self.log("--- İşlem Tamamlandı ---\n")
        
        # Listeyi otomatik yenile
        self.connect_to_tv()

    # --- 📥 APK Yükleme Bölümü ---
    def choose_and_install_apk(self):
        if not hasattr(self, 'device') or not self.device: return

        file_path, _ = QFileDialog.getOpenFileName(self, "Yüklenecek APK Dosyasını Seçin", "", "Android Paketleri (*.apk)")
        if file_path:
            self.log(f"\n[APK Kurulumu] Dosya seçildi: {os.path.basename(file_path)}")
            self.btn_install_apk.setEnabled(False)
            self.btn_install_apk.setText("Yükleniyor...")
            threading.Thread(target=self.install_apk_thread, args=(file_path,), daemon=True).start()

    def install_apk_thread(self, apk_path):
        try:
            self.log("-> Paket TV'ye aktarılıyor ve arka planda kuruluyor...")
            self.device.install(apk_path)
            self.log("-> BAŞARILI: APK TV'ye yüklendi! TV arayüzünden kontrol edebilirsiniz.")
        except Exception as e:
            self.log(f"-> YÜKLEME HATASI: {str(e)}")
        finally:
            self.btn_install_apk.setEnabled(True)
            self.btn_install_apk.setText("Bilgisayardan APK Yükle")


def main():
    app = QApplication(sys.argv)
    window = TVManagerUltimate()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()