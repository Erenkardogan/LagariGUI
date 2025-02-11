import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QPlainTextEdit
from PyQt5.QtCore import QThread, pyqtSignal
from io import StringIO
import contextlib


class WorkerThread(QThread):
    output_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        # Örnek olarak bir döngü oluşturalım
        for i in range(5):
            output = f"Döngü {i+1}"
            self.output_signal.emit(output)
            self.msleep(500)  # Yarım saniye bekle


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Output Viewer")
        self.setGeometry(100, 100, 600, 400)

        # Ana widget oluştur
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout oluştur
        layout = QVBoxLayout(central_widget)

        # Çıktı alanı (QPlainTextEdit) oluştur
        self.output_text_edit = QPlainTextEdit()
        self.output_text_edit.setReadOnly(True)  # Sadece okunabilir yap

        # Layout'a çıktı alanını ekle
        layout.addWidget(self.output_text_edit)

        # Buton oluştur ve layout'a ekle
        self.start_button = QPushButton("İşlemi Başlat")
        self.start_button.clicked.connect(self.start_worker_thread)
        layout.addWidget(self.start_button)

        # WorkerThread nesnesini oluştur
        self.worker_thread = WorkerThread()
        self.worker_thread.output_signal.connect(self.update_output)
        print("naberrrr müdürrrrr")

    def start_worker_thread(self):
        self.worker_thread.start()

    def update_output(self, text):
        # Yeni çıktıyı ekleyerek QPlainTextEdit'e yaz
        current_text = self.output_text_edit.toPlainText()
        self.output_text_edit.setPlainText(current_text + "\n" + text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
