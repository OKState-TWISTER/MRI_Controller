from PySide6 import QtWidgets, QtCore, QtNetwork
import mainwindow
import sys

if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    mw = mainwindow.MainWindow()

    mw.show()
    mw.resize(1200,800)
    mw.setMinimumSize(1200,800)

    sys.exit(app.exec())
