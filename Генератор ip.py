import sys
import random
import ipaddress  
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Генератор IP-адресов")
        self.resize(600, 300)  
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #29323c, stop: 1 #485563); color: white;") 
        
        self.setWindowIcon(QIcon("C:\\Users\\Pasha\\OneDrive\\Рабочий стол\\код\\Генератор подсетей\\ip_iconka.ico"))  # Указываем имя иконки
        self.ip_label = QLabel("", self)
        self.ip_label.setAlignment(Qt.AlignCenter)
        self.ip_label.setStyleSheet("font-size: 28px;")  

        self.ipv4_button = QPushButton("IPv4", self)  
        self.ipv4_button.setStyleSheet("background-color: #485563; color: white; border-radius: 10px;")
        self.ipv4_button.clicked.connect(lambda: self.generate_ip(4))  

        self.ipv6_button = QPushButton("IPv6", self)  
        self.ipv6_button.setStyleSheet("background-color: #485563; color: white; border-radius: 10px;")
        self.ipv6_button.clicked.connect(lambda: self.generate_ip(6))  

        self.copy_button = QPushButton("Копировать", self)
        self.copy_button.setStyleSheet("background-color: #485563; color: white; border-radius: 10px")  
        self.copy_button.clicked.connect(self.copy_ip)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.ipv4_button)
        button_layout.addWidget(self.ipv6_button)
        button_layout.addWidget(self.copy_button)

        layout = QVBoxLayout()
        layout.addWidget(self.ip_label)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def generate_ip(self, version):
        if version == 4:
            octet1 = random.randint(1, 255)
            octet2 = random.randint(0, 255)
            octet3 = random.randint(0, 255)
            octet4 = 0
            netmask = random.randint(1, 31)
            ip = f"{octet1}.{octet2}.{octet3}.{octet4}/{netmask}"
        else:
            ipv6 = ipaddress.IPv6Address(random.getrandbits(128))
            subnet = ipv6.exploded
            netmask = random.randint(1, 127)
            ip = f"{subnet}/{netmask}"
            
        self.ip_label.setText(ip)

    def copy_ip(self):
        ip_text = self.ip_label.text()
        clipboard = QApplication.clipboard()
        clipboard.setText(ip_text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
