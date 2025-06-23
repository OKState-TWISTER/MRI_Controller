# This code is V2 of the UTOL Motion Control
# Heavily Copy pasted, but reworked slightly to include a GUI
from PySide6 import QtWidgets, QtCore, QtNetwork
import mainwindow
import sys
# import UTOL_Motion_Control_pc

# @QtCore.Slot(float, float, float, float, float, float, str)
# def startMeasurement(el_start, el_stop, el_step, az_start, az_stop, az_step, measType, antenna):
#     print(f"Starting measurement! THIS IS IN MAIN!!!")

# @QtCore.Slot()
# def connectedToServer():
#     print(f"Connected to server!")
# @QtCore.Slot()
# def failedToConnect():
#     print(f"Connection to server failed!")

if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    mw = mainwindow.MainWindow()

    mw.show()
    mw.resize(1200,800)
    mw.setMinimumSize(1200,800)

    # mw.startTest.connect(startMeasurement)

    # tx_ant = QtNetwork.QTcpSocket()
    # tx_ant.connectToHost("192.168.27.154", 12345)
    # tx_ant.connected.connect(connectedToServer)
    # tx_ant.errorOccurred.connect(failedToConnect)
    # rx_ant = QtNetwork.QTcpSocket()
    # rx_ant.connectToHost("192.168.27.194", 12345)
    # rx_ant.connected.connect(connectedToServer)
    # rx_ant.errorOccurred.connect(failedToConnect)
    # Steps to run sweep:
    # generate_measurement_array -> grid, peak_val, peak_freq, az_angle, el_angle
    # move_to_start
    # sweep_2D
    #
    # Flip every other row of the matrix to fix serpentine traversal problems
    # az_angle[1::2] = az_angle[1::2, ::-1]
    # peak_freq[1::2] = peak_freq[1::2, ::-1]
    # peak_val[1::2] = peak_val[1::2, ::-1]
    #
    # Save


    sys.exit(app.exec())
