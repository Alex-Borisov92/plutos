"""Test Qt overlay directly."""
import sys
import time
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

def main():
    app = QApplication(sys.argv)
    
    window = QWidget()
    window.setWindowTitle("Plutos Test")
    window.setWindowFlags(
        Qt.FramelessWindowHint |
        Qt.WindowStaysOnTopHint |
        Qt.Tool
    )
    window.setGeometry(100, 100, 280, 100)
    window.setStyleSheet("background-color: #1a1a2e;")
    
    layout = QVBoxLayout()
    label = QLabel("D:5 | TURN!\nActive: 3 | TT")
    label.setFont(QFont("Consolas", 14, QFont.Bold))
    label.setStyleSheet("color: #FFFF00; padding: 10px;")
    label.setAlignment(Qt.AlignCenter)
    layout.addWidget(label)
    
    window.setLayout(layout)
    window.show()
    
    print("Qt overlay window should be visible at (100, 100)")
    print("Press Ctrl+C to exit")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
