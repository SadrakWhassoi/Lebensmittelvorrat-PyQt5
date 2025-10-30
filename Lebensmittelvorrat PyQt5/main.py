import sys
from PyQt5.QtWidgets import QApplication
from ui_main import MainWindow

app = QApplication(sys.argv)

# Fenster erstellen und anzeigen
window = MainWindow()
window.show()

# Event-Loop starten
sys.exit(app.exec_())