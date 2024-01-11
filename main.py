import sys

from PySide6 import QtWidgets
from qt_material import apply_stylesheet

from bot_automacao.main_window import MainWindow

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    widget = MainWindow()
    apply_stylesheet(app, theme='dark_blue.xml')
    widget.show()
    sys.exit(app.exec())
