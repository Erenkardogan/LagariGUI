from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QPushButton
from Ui_mainWindow import Ui_MainWindow
import sys
from PyQt5.QtSerialPort import QSerialPortInfo, QSerialPort
from PyQt5.QtCore import QIODevice, QTimer, QThread, pyqtSignal
from dronekit import connect, VehicleMode
import time


# Uygulamanın İHA'yı arm etmeye çalışırken donmaması için QThread modülünü kullandık.
class ArmThread(QThread):
    armed = pyqtSignal(bool)

    def __init__(self, vehicle):
        super().__init__()
        self.vehicle = vehicle

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


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.listSerialPorts)
        self.timer.start(1000)
        self.listSerialPorts()
        # serialPort adında bir nesne oluşturdum çünkü com portları bağlanmada kullanılacak
        self.serialPort = QSerialPort()
        self.setWindowTitle("LAGARİUAV")

        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>Genel kod ayarlaması<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        # Başlangıçta solda sadece butonların olduğu menu kısmını göstermek için isim olanı gizledik.
        self.leftMenu_name.setHidden(True)

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

        # >>>>>>>>>>>>>>>>>>>>>>>>Ayarlar sayfası kodları<<<<<<<<<<<<<<<<<<<<<<<<<<
        # Butonların başlangıçta işlevsiz olması için değerleri False yapıldı<<<<<
        self.pushButton_10.setEnabled(False)
        self.pushButton_11.setEnabled(False)
        self.pushButton_12.setEnabled(False)

        # CheckBox'ların görevleri yazıldı
        self.checkBox.clicked.connect(self.control_checkBox)
        self.checkBox_2.clicked.connect(self.control_checkBox2)
        self.checkBox_3.clicked.connect(self.control_checkBox3)

        # Butona tıklandığında disabled olması için kod yazıldı
        self.pushButton_10.clicked.connect(self.portConnect)
        self.pushButton_11.clicked.connect(self.arm_et)
        self.pushButton_12.clicked.connect(self.auto_mode_al)

    # Check Box'a tıklandığında butonun aktifliğini hazırlayan fonksiyonlar yazıldı
    # Butona tıklandığında check box'ın işlevini kapatıp butonu deactive eden fonksiyonlar yazıldı
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
            self.vehicle.mode = VehicleMode('GUIDED')
            self.pushButton_12.setEnabled(False)
            self.checkBox_3.setChecked(False)
        except Exception as e:
            print("sorun:", e)
            if self.vehicle.mode == VehicleMode('GUIDED'):
                print("AUTO mode alındı")
            else:
                print("Maalesef bağlı değil")

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

    # DroneKit fonksiyonları
    def connectMyPlane(self):
        # parser = argparse.ArgumentParser(description='commands')
        # parser.add_argument('--connect', default='tcp:127.0.0.1:5762')
        # parser.add_argument('--connect', default="self.comboBox.currentText()")
        # args = parser.parse_args()

        connection_string = 'tcp:127.0.0.1:5762'
        # connection_string = self.comboBox.currentText()
        baud_rate = int(self.comboBox_2.currentText())

        self.vehicle = connect(connection_string, baud=baud_rate, wait_ready=True, timeout=100)
        print("KKKKKKK")
        return self.vehicle


# Execute App
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())





