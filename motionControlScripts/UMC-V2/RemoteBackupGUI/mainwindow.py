import sys
import random
from PySide6 import QtCore, QtWidgets, QtGui, QtNetwork
from PySide6.QtCore import QThread
# from matplotlib import pyplot as plt
from sweepControlv2 import sweepControl

from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.backends.backend_qtagg import \
    NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.qt_compat import QtWidgets
from matplotlib.figure import Figure
from matplotlib import cm
import numpy as np
import scipy
import json
from logger import logger

class MainWindow(QtWidgets.QWidget):
    responseRecv = QtCore.Signal(bool, str, float)
    cmdTimedOut = QtCore.Signal()
    def __init__(self):
        super().__init__()

        self.log = logger()
        
        self.sweepController = None
        self.readBuffer = QtCore.QByteArray()

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.manual_group = QtWidgets.QGroupBox("Manual Control", self)
        self.info_group = QtWidgets.QGroupBox("Information", self)
        self.main_layout.addWidget(self.info_group)
        self.main_layout.addWidget(self.manual_group)

        # Build out the manual group
        self.manual_font = QtGui.QFont()
        self.manual_font.setPointSize(24)
        self.manual_up = QtWidgets.QPushButton("Up", self.manual_group)
        self.manual_up.setFont(self.manual_font)
        self.manual_down = QtWidgets.QPushButton("Down", self.manual_group)
        self.manual_down.setFont(self.manual_font)
        self.manual_left = QtWidgets.QPushButton("Left", self.manual_group)
        self.manual_left.setFont(self.manual_font)
        self.manual_right = QtWidgets.QPushButton("Right", self.manual_group)
        self.manual_right.setFont(self.manual_font)
        self.manual_step_frame = QtWidgets.QFrame(self.manual_group)
        self.manual_step_layout = QtWidgets.QHBoxLayout(self.manual_step_frame)
        self.manual_step_label = QtWidgets.QLabel("Step Size:")
        self.manual_step_label.setFont(self.manual_font)
        self.manual_step_layout.addWidget(self.manual_step_label)
        self.manual_step_text = QtWidgets.QLineEdit(text="0.1")
        self.manual_step_text.setFont(self.manual_font)
        self.manual_step_layout.addWidget(self.manual_step_text)
        # self.manual_meas_jitter = QtWidgets.QPushButton("Measure Jitter", self.manual_group)
        self.manual_set_home = QtWidgets.QPushButton("Set Zero", self.manual_group)
        self.manual_set_home.setFont(self.manual_font)

        self.info_font = QtGui.QFont()
        self.info_font.setPointSize(24)
        self.info_group_layout = QtWidgets.QVBoxLayout(self.info_group)
        self.info_az_label = QtWidgets.QLabel("Azimuth: -0.0000")
        self.info_az_label.setFont(self.info_font)
        self.info_group_layout.addWidget(self.info_az_label)
        self.info_el_label = QtWidgets.QLabel("Elevation: -0.0000")
        self.info_el_label.setFont(self.info_font)
        self.info_group_layout.addWidget(self.info_el_label)
        self.info_idx_label = QtWidgets.QLabel("Index: -0.0000")
        self.info_idx_label.setFont(self.info_font)
        self.info_group_layout.addWidget(self.info_idx_label)
        self.info_enc_raw_label = QtWidgets.QLabel("RAW ENCODER: -0.0000")
        self.info_enc_raw_label.setFont(self.info_font)
        self.info_group_layout.addWidget(self.info_enc_raw_label)

        # self.tx_ant = QtNetwork.QAbstractSocket(QtNetwork.QAbstractSocket.SocketType.UnknownSocketType, self)
        self.tx_ant = QtNetwork.QTcpSocket()
        self.tx_ant.connectToHost("192.168.27.194", 12345)
        self.tx_ant.connected.connect(self.connectedToServer_tx)
        self.tx_ant.errorOccurred.connect(self.failedToConnect_tx)


        # CONNECTIONS
        self.manual_up.clicked.connect(self.up_btn_clicked)
        self.manual_left.clicked.connect(self.left_btn_clicked)
        self.manual_right.clicked.connect(self.right_btn_clicked)
        self.manual_down.clicked.connect(self.down_btn_clicked)
        self.manual_set_home.clicked.connect(self.set_home_clicked)

        self.tx_reconn_timer = QtCore.QTimer(self)
        self.tx_reconn_timer.setSingleShot(True)
        self.tx_reconn_timer.setInterval(5000)
        self.tx_reconn_timer.timeout.connect(self.reconn_Tx)

        self.cmd_timer = QtCore.QTimer()
        self.cmd_timer.setSingleShot(True)
        self.cmd_timer.setInterval(30000)
        self.cmd_timer.timeout.connect(self.on_cmd_timeout)

        # Calling this to default the manual control window to the TX antenna
        self.ant_sock = self.tx_ant
        self.ant_sock.readyRead.connect(self.on_tcp_data)

    
    def paintEvent(self, event):
        self.manual_group.setFixedHeight(self.height()/2)
        # self.manual_group.move(0, 3*self.height()/4)

        #Layout the Manual Group
        self.manual_right.setFixedWidth(self.width() / 4)
        self.manual_left.setFixedWidth(self.width() / 4)
        self.manual_down.setFixedWidth(self.width() / 4)
        self.manual_up.setFixedWidth(self.width() / 4)

        self.manual_up.move(int(self.manual_group.width()/2 - self.manual_up.width()/2), 20)
        self.manual_left.move(self.manual_up.x() - self.manual_left.width(), self.manual_up.y() + self.manual_up.height())
        self.manual_right.move(self.manual_up.x() + self.manual_left.width(), self.manual_up.y() + self.manual_up.height())
        self.manual_down.move(self.manual_up.x(), self.manual_up.y() + 2 * self.manual_up.height())

        self.manual_set_home.setFixedWidth(self.manual_step_frame.width())
        self.manual_set_home.move(self.width() / 2 - self.manual_set_home.width() / 2, self.height() / 4)
        self.manual_step_frame.move(self.width() / 2 - self.manual_set_home.width() / 2, self.height() / 4 + self.manual_set_home.height() + 10)



        return super().paintEvent(event)


    @QtCore.Slot()
    def connectedToServer_tx(self):
        self.log.info(f"Connected to TX server!")
    @QtCore.Slot()
    def failedToConnect_tx(self, err):
        self.log.error(f"Connection to TX server failed!\n\t{err}")
        self.tx_reconn_timer.start()
        # self.tx_ant.connectToHost("192.168.27.155", 12345)
    @QtCore.Slot()
    def reconn_Tx(self):
        self.log.warn(f"Attempting to reconnect Tx")
        self.tx_ant.connectToHost("192.168.27.155", 12345)

    
    @QtCore.Slot()
    def on_new_location(self, az, el):
        self.info_az_label.setText(f"Azimuth: {az:.04f}")
        self.info_el_label.setText(f"Elevation: {el:.04f}")
    @QtCore.Slot()
    def on_new_az(self, az):
        self.info_az_label.setText(f"Azimuth: {az:.04f}")
    @QtCore.Slot()
    def on_new_el(self, el):
        self.info_el_label.setText(f"Elevation: {el:.04f}")

    @QtCore.Slot()
    def start_btn_clicked(self):

        measType = "waveform" if self.controls_typeSelect_waveform.isChecked() else "fft_peaks"
        antSweeping = "receiver" if self.controls_antSelect_rx.isChecked() else "transmitter"
        self.ant_sock = None
        if (antSweeping == "receiver"):
            self.ant_sock = self.rx_ant
        else:
            self.ant_sock = self.tx_ant
        if self.ant_sock.bytesAvailable():
            self.ant_sock.readAll()
        az_start = float(self.controls_az_start_text.text())
        az_stop = float(self.controls_az_stop_text.text())
        az_step = float(self.controls_az_step_text.text())
        
        el_start = float(self.controls_el_start_text.text())
        el_stop = float(self.controls_el_stop_text.text())
        el_step = float(self.controls_el_step_text.text())

        sweeptype = None
        if self.controls_sweepType_grid.isChecked():
            sweeptype = "grid"
        else:
            sweeptype = "serpentine"

        self.startMeasurement(el_start, el_stop, el_step, az_start, az_stop, az_step, measType, antSweeping, sweeptype)
    
    @QtCore.Slot()
    def up_btn_clicked(self):
        ant = "transmitter"
        step = float(self.manual_step_text.text())
        self.log.info(f"{ant} up {step} degrees")
        self.ant_sock.write(f'move_el_DM542T.py:{step}'.encode())
    
    @QtCore.Slot()
    def down_btn_clicked(self):
        ant = "transmitter"
        step = float(self.manual_step_text.text())
        self.log.info(f"{ant} down {step} degrees")
        self.ant_sock.write(f'move_el_DM542T.py:{-1 * step}'.encode())
    
    @QtCore.Slot()
    def left_btn_clicked(self):
        ant = "transmitter"
        step = float(self.manual_step_text.text())
        self.log.info(f"{ant} left {step} degrees")
        self.ant_sock.write(f'move_az_DM542T.py:{-1 * step}'.encode())
    
    @QtCore.Slot()
    def right_btn_clicked(self):
        ant = "transmitter"
        step = float(self.manual_step_text.text())
        self.log.info(f"{ant} right {step} degrees")
        self.ant_sock.write(f'move_az_DM542T.py:{step}'.encode())
    
    @QtCore.Slot()
    def set_home_clicked(self):
        ant = "transmitter"
        self.log.info(f"{ant} set zero")
        self.ant_sock.write(f'set_home:0'.encode())

    @QtCore.Slot()
    def measure_jitter(self):
        self.ant_sock.write(f"measure_jitter:0".encode())
    
    @QtCore.Slot()
    def onNewData(self):
        if self.surf_plot is None:
            self.surf_plot = self.plot_ax.plot_surface(self.sweepController.az_angle, self.sweepController.el_angle, self.sweepController.peak_val, cmap = cm.coolwarm)
        else:

            az_angle = self.sweepController.grid.get_az_angle_grid()
            el_angle = self.sweepController.grid.get_el_angle_grid()
            peak_val = self.sweepController.grid.get_peak_val_grid()

            self.surf_plot.remove()
            self.surf_plot = self.plot_ax.plot_surface(az_angle, el_angle, peak_val, cmap = cm.coolwarm)
            self.plot_static.draw()

    @QtCore.Slot()
    def save_plot(self):
        if self.sweepController is None:
            self.log.error(f"NO DATA COLLECTED TO SAVE")
            return
        self.log.info(f"Saving plot")
        fd = QtWidgets.QFileDialog.getSaveFileName(self,filter="Matlab Files (*.mat)")

        self.log.debug(f"File Destination: {fd}")

        if fd[0] != "":

            mdict = {
                'peak_val': self.sweepController.grid.get_peak_val_grid(),
                'peak_freq': self.sweepController.grid.get_peak_freq_grid(),
                'az_angle': self.sweepController.grid.get_az_angle_grid(),
                'el_angle': self.sweepController.grid.get_el_angle_grid(),
                'point_idx': self.sweepController.grid.get_idx_grid()
            }

            scipy.io.savemat(f"{fd[0]}", mdict)

    def save_jitter(self, time, val):
        self.log.info(f"Saving jitter")
        fd = QtWidgets.QFileDialog.getSaveFileName(self,filter="Matlab Files (*.mat)")

        self.log.debug(f"File Destination: {fd}")
        mdict = {
            'timestamp': time,
            'readings': val
        }
        scipy.io.savemat(f"{fd[0]}", mdict)



    @QtCore.Slot(float, float)
    def update_loc(self, az, el):
        self.log.debug(f"New Location:\n\tAz: {az}\n\tEl: {el}")

    @QtCore.Slot(str)
    def send_cmd(self, cmd):
        # if self.ant_sock.bytesAvailable() > 0:
        #     _ = self.ant_sock.readAll()
        self.log.debug(f"Sending Command {cmd}")
        if self.ant_sock.bytesAvailable:
            self.ant_sock.readAll()
        self.ant_sock.write(cmd.encode())
        self.ant_sock.flush()
        self.last_cmd = cmd
        self.cmd_timer.start()

    @QtCore.Slot()
    def on_tcp_data(self):
        res = QtCore.QByteArray()
        res.append(self.ant_sock.readAll())
        check = res[-5:].data().decode()
        self.readBuffer.append(res)
        if check != "/UTOL":
            return
        self.cmd_timer.stop()
        res = self.readBuffer
        
        if res.isNull():
            self.log.error(f"NULL BYTES FROM TCP SOCKET")
            return False, None
        res_str = res.data().decode().replace("/UTOL","")
        self.log.debug(f"RES_STR: {res_str}")
        f = open("test.txt", "w")
        f.write(res_str)
        f.close()
        data = json.loads(res_str)
        self.log.debug(f"JSON PARSED DATA: {data}")

        if data['cmd'].find("move") >= 0: #Then we sent a move cmd
            cmd_succ = data['results']['success']
            cmd_plane = "el" if data['cmd'].find('el') >= 0 else "az"
            cmd_angle = float(data['results']['change'])
            if cmd_plane == "el":
                self.info_enc_raw_label.setText(f"RAW ENCODER: {data['results']['raw']}")
                self.on_new_el(data['results']['change'])
            if cmd_plane == "az":
                self.on_new_az(data['results']['change'])
            self.responseRecv.emit(cmd_succ, cmd_plane, cmd_angle)
        elif data['cmd'] == 'set_home':
            self.homeSet.emit()
        elif data['cmd'] == 'measure_jitter':
            self.save_jitter(data['results']['time'], data['results']['readings'])
            
        self.readBuffer = QtCore.QByteArray()


    @QtCore.Slot()
    def on_sweep_finished(self):
        self.save_plot()

    @QtCore.Slot()
    def on_cmd_timeout(self):
        self.log.warn(f"Command timed out. Resending...")
        self.send_cmd(self.last_cmd)

    @QtCore.Slot()
    def toggle_pause(self):
        if self.controls_pauseButton.text() == "Pause Sweep":
            self.controls_pauseButton.setText("Resume Sweep")
        else:
            self.controls_pauseButton.setText("Pause Sweep")
            

if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = MainWindow()
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())