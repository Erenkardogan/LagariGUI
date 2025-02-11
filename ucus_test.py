from PyQt5.QtWidgets import *
from Ui_mainWindow2 import Ui_MainWindow
import sys
from PyQt5.QtSerialPort import *
from PyQt5.QtCore import *
from dronekit import connect, VehicleMode
import time
from PyQt5.QtGui import *
import cv2


# Auto mode alınırken thread kullanılır
class AutoModeThread(QThread):
    auto = pyqtSignal(bool)

    def __init__(self, vehicle):
        super().__init__()
        self.vehicle = vehicle

    # run kısmını değiştirmeyin tüm threadlerde run() olması lazım bu kısım thread çağırıldığında çalışan kısımdır
    def run(self):
        self.automa()

    # Auto mode almak için kullanılan fonksiyon yazıldı
    def automa(self):
        self.vehicle.mode = VehicleMode('AUTO')
        time.sleep(1)
        print("Vehicle is Auto")
        self.auto.emit(True)


# RTL mode alınırken uzun sürerse donmaması için thread modülü kullanılır
class RtlModeThread(QThread):
    rtl = pyqtSignal(bool)

    def __init__(self, vehicle):
        super().__init__()
        self.vehicle = vehicle

    # run kısmını değiştirmeyin tüm threadlerde run() olması lazım bu kısım thread çağırıldığında çalışan kısımdır
    def run(self):
        self.rtlma()

    # RTL mode alma fonksiyonu yazıldı
    def rtlma(self):
        while self.vehicle.mode != VehicleMode('RTL'):
            print("Waiting for the RTL mode")
            self.vehicle.mode = VehicleMode('RTL')
            time.sleep(1)
        print("Vehicle is RTL")
        self.rtl.emit(True)


# Uygulamanın İHA'yı arm etmeye çalışırken donmaması için QThread modülünü kullandık.
class ArmThread(QThread):
    armed = pyqtSignal(bool)

    def __init__(self, vehicle):
        super().__init__()
        self.vehicle = vehicle

    # run kısmını değiştirmeyin tüm threadlerde run() olması lazım bu kısım thread çağırıldığında çalışan kısımdır
    def run(self):
        self.arm()

    # İHA arm fonksiyonu
    def arm(self):
        print("Vehicle is armable")
        # Uygun bir durum sağlandığında döngüden çıkılmalıdır
        while self.vehicle.armed == False:
            print("Waiting for vehicle to arm")
            self.vehicle.armed = True  # İHA'yı arm etmeye çalışıyoruz
            time.sleep(1)
        print("Vehicle is armed")
        self.armed.emit(True)


# İHA'dan verileri almak için thread modülü kullandık.
class VehicleDataThread(QThread):
    dataChanged = pyqtSignal(float, float, int)

    def __init__(self, vehicle):
        super().__init__()
        self.vehicle = vehicle

    # run kısmını değiştirmeyin tüm threadlerde run() olması lazım bu kısım thread çağırıldığında çalışan kısımdır
    def run(self):
        while True:  # Thread sürekli olarak çalışacak
            # İHA'dan hız, yükseklik ve batarya seviyesi verisini al
            speed = self.getSpeed()
            altitude = self.getAltitude()
            battery_level = self.getBatteryLevel()

            # Sinyali emit ederek verileri gönder
            self.dataChanged.emit(speed, altitude, battery_level)

            self.sleep(1)  # 1 saniye bekleme

    # Hız verisini almak için fonksiyon oluşturduk
    def getSpeed(self):
        if self.vehicle is not None:
            return self.vehicle.airspeed
        else:
            return 0.0

    # Yükseklik verisini almak için fonksiyon oluşturduk
    def getAltitude(self):
        if self.vehicle is not None:
            return self.vehicle.location.global_relative_frame.alt
        else:
            return 0.0

    # batarya seviyesi verisini almak için fonksiyon oluşturduk
    def getBatteryLevel(self):
        if self.vehicle is not None and self.vehicle.battery is not None:
            return self.vehicle.battery.level
        else:
            return 0

    # Tüm verilerin işlendiği fonksiyon yazıldı( Gerektiğinde kullanılabilir)
    def getVehicleData(self):
        # Burada İHA'dan hız verisi alınacak kodu yazın
        if self.vehicle is not None:
            speed = self.vehicle.airspeed
            altitude = self.vehicle.location.global_relative_frame.alt
            battery_level = self.vehicle.battery
            data = [speed, altitude, battery_level]
            return data
        else:
            return 0.0


# Uygulamanın İHA'dan kamera görüntüsü almaya çalışırken donmaması için QThread modülünü kullandık.
class CameraViewThread1(QThread):
    ImageUpdate = pyqtSignal(QImage)

    # Opencv ile görüntü aktarım kodu yazıldı
    def run(self):
        self.ThreadActive = True
        Capture = cv2.VideoCapture(0) # Kamera görüntüsü açmak için kanal 0 seçildi
        while self.ThreadActive:
            ret, frame = Capture.read()
            if not ret:
                print("Kamera görüntüsü alınamadı.")
            if ret:
                Image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Görüntü 3 kanallı(RGB) görüntüye çevrildi
                FlippedImage = cv2.flip(Image, 1)
                ConvertToQtFormat = QImage(FlippedImage.data, FlippedImage.shape[1], FlippedImage.shape[0], QImage.Format_RGB888)
                Pic = ConvertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)
                self.ImageUpdate.emit(Pic)


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.listSerialPorts)
        self.timer.start(1000)
        self.listSerialPorts()
        self.showFullScreen()
        # serialPort adında bir nesne oluşturdum çünkü com portları bağlanmada kullanılacak
        self.serialPort = QSerialPort()
        self.setWindowTitle("LAGARİUAV")
        self.vehicle = None
        self.data_thread = None
        # Ekran boyutunu tam ekran yapmak için kod ayarlandı.
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        # Pencere boyutunu ekran boyutuna ayarla
        self.resize(screen_geometry.width(), screen_geometry.height() - 40)

        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>Genel kod ayarlaması<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        # Başlangıçta solda sadece butonların olduğu menu kısmını göstermek için isim olanı gizledik.
        self.leftMenu_name.setHidden(True)

        # >>>>>>>>>>>>>>>>>Sekmeler Bölümü kodları<<<<<<<<<<<<<<<<<<
        # Uygulamayı kapatma butonuna görev atandı
        self.pushButton_8.clicked.connect(self.close)
        self.pushButton_4.clicked.connect(self.close)

        # Sekmeler arası geçiş için butonlara görev atandı
        self.pushButton.clicked.connect(self.switch_to_kontrolPaneli)
        self.pushButton_5.clicked.connect(self.switch_to_kontrolPaneli)

        self.pushButton_2.clicked.connect(self.switch_to_kamera)
        self.pushButton_6.clicked.connect(self.switch_to_kamera)

        self.pushButton_7.clicked.connect(self.switch_to_ayarlar)
        self.pushButton_3.clicked.connect(self.switch_to_ayarlar)

        # >>>>>>>>>>>>>>>>>>>>Görev Algoritmaları bölümü<<<<<<<<<<<<<<<<<<<<<<<<<<
        # Butonların başlangıçta işlevsiz olması için değerleri False yapıldı<<<<<
        self.pushButton_10.setEnabled(False)
        self.pushButton_11.setEnabled(False)
        self.pushButton_12.setEnabled(False)
        self.pushButton_13.setEnabled(False)
        self.pushButton_14.setEnabled(False)
        self.pushButton_16.setEnabled(False)
        self.pushButton_17.setEnabled(False)
        self.pushButton_18.setEnabled(False)
        self.pushButton_19.setEnabled(False)
        self.pushButton_20.setEnabled(False)

        # CheckBox'ların görevleri yazıldı
        self.checkBox.clicked.connect(self.control_checkBox)
        self.checkBox_2.clicked.connect(self.control_checkBox2)
        self.checkBox_3.clicked.connect(self.control_checkBox3)
        self.checkBox_4.clicked.connect(self.control_checkBox4)
        self.checkBox_5.clicked.connect(self.control_checkBox5)
        self.checkBox_7.clicked.connect(self.control_checkBox7)
        self.checkBox_6.clicked.connect(self.control_checkBox6)
        self.checkBox_8.clicked.connect(self.control_checkBox8)
        self.checkBox_9.clicked.connect(self.control_checkBox9)
        self.checkBox_10.clicked.connect(self.control_checkBox10)

        # Butona tıklandığında gerekli fonksiyonu çağırması için kod yazıldı
        self.pushButton_10.clicked.connect(self.portConnect)
        self.pushButton_11.clicked.connect(self.arm_et)
        self.pushButton_12.clicked.connect(self.auto_mode_al)
        self.pushButton_19.clicked.connect(self.rtl_mode_al)
        self.pushButton_21.clicked.connect(self.veriyial)

    # >>>>>>>>>>>>>>>>>>>>>>>>>Kamera görüntüsü için fonksiyonlar<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        # Kamera görüntüsü için Thread class'ını çağırma
        self.camera_thread = CameraViewThread1()
        self.camera_thread.start()
        self.camera_thread.ImageUpdate.connect(self.ImageUpdateSlot)

    # Kamera görüntüsünü uygulamaya yerleştirmek için label'a görüntü girdisi fonksiyonu yazıldı
    def ImageUpdateSlot(self, Image):
        self.label_15.setPixmap(QPixmap.fromImage(Image))
        self.label_32.setPixmap(QPixmap.fromImage(Image))

    # Check Box'a tıklandığında butonun aktifliğini hazırlayan fonksiyonlar yazıldı
    # Check box'ı kontrol ederek eğer açıksa butonu aktive kapalıysa butonu deaktive eden fonksiyonlar yazıldı
    def control_checkBox(self):
        if self.checkBox.isChecked():
            self.pushButton_10.setEnabled(True)
        else:
            self.pushButton_10.setEnabled(False)

    def control_checkBox2(self):
        if self.checkBox_2.isChecked():
            self.pushButton_11.setEnabled(True)
        else:
            self.pushButton_11.setEnabled(False)

    def control_checkBox3(self):
        if self.checkBox_3.isChecked():
            self.pushButton_12.setEnabled(True)
        else:
            self.pushButton_12.setEnabled(False)

    def control_checkBox4(self):
        if self.checkBox_4.isChecked():
            self.pushButton_16.setEnabled(True)
        else:
            self.pushButton_16.setEnabled(False)

    def control_checkBox5(self):
        if self.checkBox_5.isChecked():
            self.pushButton_17.setEnabled(True)
        else:
            self.pushButton_17.setEnabled(False)

    def control_checkBox7(self):
        if self.checkBox_7.isChecked():
            self.pushButton_18.setEnabled(True)
        else:
            self.pushButton_18.setEnabled(False)

    def control_checkBox6(self):
        if self.checkBox_6.isChecked():
            self.pushButton_20.setEnabled(True)
        else:
            self.pushButton_20.setEnabled(False)

    def control_checkBox8(self):
        if self.checkBox_8.isChecked():
            self.pushButton_13.setEnabled(True)
        else:
            self.pushButton_13.setEnabled(False)

    def control_checkBox9(self):
        if self.checkBox_9.isChecked():
            self.pushButton_14.setEnabled(True)
        else:
            self.pushButton_14.setEnabled(False)

    def control_checkBox10(self):
        if self.checkBox_10.isChecked():
            self.pushButton_19.setEnabled(True)
        else:
            self.pushButton_19.setEnabled(False)

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>Butonların işlevleri için fonksiyonlar yazıldı<<<<<<<<<<<<<<<<<><<<<<<<<<<<<
    # İHA bağlantı butonuna tıklandığında port ve baudRate girdisi alınarak İHA'ya bağlanma fonksiyonunu çağırır.
    def portConnect(self):
        try:
            self.serialPort = QSerialPort()
            # self.serialPort.setPortName(self.comboBox.currentText())
            # self.serialPort.setBaudRate(int(self.comboBox_2.currentText()))
            if not self.serialPort.isOpen():
                print("İHA'ya bağlanılıyor")
                self.serialPort.open(QIODevice.ReadWrite)
                self.vehicle = self.connectMyPlane()
                self.pushButton_10.setEnabled(False)
                self.checkBox.setChecked(False)
        except Exception as e:
            print("Hata:", e)

    # ARM ET butonuna tıklandığında İHA'ya arm etme sinyalini gönderen fonksiyon yazıldı
    def arm_et(self):
        try:
            self.arm_thread = ArmThread(self.vehicle)
            self.arm_thread.start()
            self.pushButton_11.setEnabled(False)
            self.checkBox_2.setChecked(False)
        except Exception as e:
            print("Connection not established yet:", e)

    # Butona basıldığı vakit auto mode alma işlemini yapacak fonksiyon yazıldı
    def auto_mode_al(self):
        try:
            self.auto_thread = AutoModeThread(self.vehicle)
            self.auto_thread.start()
            self.pushButton_12.setEnabled(False)
            self.checkBox_3.setChecked(False)
        except Exception as e:
            print("sorun:", e)

    # Butona basıldığı vakit RTL mode alma işlemini yapacak fonksiyon yazıldı
    def rtl_mode_al(self):
        try:
            self.rtl_thread = RtlModeThread(self.vehicle)
            self.rtl_thread.start()
            self.pushButton_19.setEnabled(False)
            self.checkBox_10.setChecked(False)
        except Exception as e:
            print("sorun:", e)

    # Veriyi Al Butonuna basıldığı vakit verilerin alındığı fonksiyon
    def veriyial(self):
        # VehicleDataThread örneği oluştur ve bağlantıyı kur
        self.data_thread = VehicleDataThread(self.vehicle)
        self.data_thread.dataChanged.connect(self.updateDataDisplay)  # Veri değiştiğinde updateDataDisplay metodunu çağır
        self.data_thread.start()  # Thread'i başlat

    # Verilerin çıktılarını displayde göstermek için gerekli fonksiyon yazıldı
    def updateDataDisplay(self, speed, altitude, battery_level):
        # Verileri arayüz bileşenlerine göster
        self.lcdNumber_2.display(speed)
        self.lcdNumber_3.display(altitude)
        if battery_level is not None:
            self.progressBar.setValue(int(battery_level))  # Batarya seviyesini progress bar ile göstermek için
        else:
             self.progressBar_battery.setValue(0)

    # combo Box içerisine bilgisayara bağlı portları eklemek için fonksiyon yazıldı
    def listSerialPorts(self):
        self.comboBox.clear()
        serialPortInfo = QSerialPortInfo()
        for serialPort in serialPortInfo.availablePorts():
            self.comboBox.addItem(serialPort.portName())

    # Sekmeler arası geçiş için fonksiyonlar atandı
    def switch_to_kontrolPaneli(self):
        self.stackedWidget.setCurrentIndex(0)

    def switch_to_kamera(self):
        self.stackedWidget.setCurrentIndex(1)

    def switch_to_ayarlar(self):
        self.stackedWidget.setCurrentIndex(2)

    # Dronekit fonksiyonu İHA bağlantısı için
    def connectMyPlane(self):
        # parser = argparse.ArgumentParser(description='commands')
        # parser.add_argument('--connect', default='tcp:127.0.0.1:5762')
        # parser.add_argument('--connect', default="self.comboBox.currentText()")
        # args = parser.parse_args()

        # connection_string = 'tcp:127.0.0.1:5762'
        connection_string = self.comboBox.currentText()
        baud_rate = int(self.comboBox_2.currentText())

        self.vehicle = connect(connection_string, baud=baud_rate, wait_ready=True, timeout=100, heartbeat_timeout=100)
        print("İHA'ya bağlandı")
        return self.vehicle


# Execute App
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())





