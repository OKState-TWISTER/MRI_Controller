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

class MainWindow(QtWidgets.QWidget):
    startTest = QtCore.Signal(float, float, float, float, float, float, str, str)
    responseRecv = QtCore.Signal(bool, str, float)
    
    def __init__(self):
        super().__init__()
        
        self.sweepController = None

        self.controls_group = QtWidgets.QGroupBox("Sweep Controls", self)
        self.plot_group = QtWidgets.QGroupBox("Plot", self)
        self.manual_group = QtWidgets.QGroupBox("Manual Control", self)
        self.info_group = QtWidgets.QGroupBox("Information", self)

        # Build out the controls group
        self.controls_layout = QtWidgets.QVBoxLayout(self.controls_group)
        self.controls_typeSelect_group = QtWidgets.QGroupBox("Measurment Type")
        self.controls_layout.addWidget(self.controls_typeSelect_group)
        self.controls_antSelect_group = QtWidgets.QGroupBox("Antenna")
        self.controls_layout.addWidget(self.controls_antSelect_group)

        self.controls_typeSelect_layout = QtWidgets.QVBoxLayout(self.controls_typeSelect_group)
        self.controls_typeSelect_waveform = QtWidgets.QRadioButton("Waveform")
        self.controls_typeSelect_waveform.setChecked(True)
        self.controls_typeSelect_fftPeaks = QtWidgets.QRadioButton("FFT Peaks")
        self.controls_typeSelect_layout.addWidget(self.controls_typeSelect_waveform)
        self.controls_typeSelect_layout.addWidget(self.controls_typeSelect_fftPeaks)
        
        self.controls_antSelect_layout = QtWidgets.QVBoxLayout(self.controls_antSelect_group)
        self.controls_antSelect_tx = QtWidgets.QRadioButton("Transmitter")
        self.controls_antSelect_tx.setChecked(True)
        self.controls_antSelect_rx = QtWidgets.QRadioButton("Receiver")
        self.controls_antSelect_layout.addWidget(self.controls_antSelect_tx)
        self.controls_antSelect_layout.addWidget(self.controls_antSelect_rx)

        self.controls_az_group = QtWidgets.QGroupBox("Azimuth")
        self.controls_layout.addWidget(self.controls_az_group)
        self.controls_az_layout = QtWidgets.QVBoxLayout(self.controls_az_group)
        self.controls_az_start_frame = QtWidgets.QFrame()
        self.controls_az_layout.addWidget(self.controls_az_start_frame)
        self.controls_az_stop_frame = QtWidgets.QFrame()
        self.controls_az_layout.addWidget(self.controls_az_stop_frame)
        self.controls_az_step_frame = QtWidgets.QFrame()
        self.controls_az_layout.addWidget(self.controls_az_step_frame)
        self.controls_az_start_layout = QtWidgets.QHBoxLayout(self.controls_az_start_frame)
        self.controls_az_start_label = QtWidgets.QLabel("Start")
        self.controls_az_start_layout.addWidget(self.controls_az_start_label)
        self.controls_az_start_text = QtWidgets.QLineEdit(text="-1.0")
        self.controls_az_start_layout.addWidget(self.controls_az_start_text)
        self.controls_az_stop_layout = QtWidgets.QHBoxLayout(self.controls_az_stop_frame)
        self.controls_az_stop_label = QtWidgets.QLabel("Stop")
        self.controls_az_stop_layout.addWidget(self.controls_az_stop_label)
        self.controls_az_stop_text = QtWidgets.QLineEdit(text="1.0")
        self.controls_az_stop_layout.addWidget(self.controls_az_stop_text)
        self.controls_az_step_layout = QtWidgets.QHBoxLayout(self.controls_az_step_frame)
        self.controls_az_step_label = QtWidgets.QLabel("Step")
        self.controls_az_step_layout.addWidget(self.controls_az_step_label)
        self.controls_az_step_text = QtWidgets.QLineEdit(text="1.0")
        self.controls_az_step_layout.addWidget(self.controls_az_step_text)

        self.controls_el_group = QtWidgets.QGroupBox("Elevation")
        self.controls_layout.addWidget(self.controls_el_group)
        self.controls_el_layout = QtWidgets.QVBoxLayout(self.controls_el_group)
        self.controls_el_start_frame = QtWidgets.QFrame()
        self.controls_el_layout.addWidget(self.controls_el_start_frame)
        self.controls_el_stop_frame = QtWidgets.QFrame()
        self.controls_el_layout.addWidget(self.controls_el_stop_frame)
        self.controls_el_step_frame = QtWidgets.QFrame()
        self.controls_el_layout.addWidget(self.controls_el_step_frame)
        self.controls_el_start_layout = QtWidgets.QHBoxLayout(self.controls_el_start_frame)
        self.controls_el_start_label = QtWidgets.QLabel("Start")
        self.controls_el_start_layout.addWidget(self.controls_el_start_label)
        self.controls_el_start_text = QtWidgets.QLineEdit(text="-1.0")
        self.controls_el_start_layout.addWidget(self.controls_el_start_text)
        self.controls_el_stop_layout = QtWidgets.QHBoxLayout(self.controls_el_stop_frame)
        self.controls_el_stop_label = QtWidgets.QLabel("Stop")
        self.controls_el_stop_layout.addWidget(self.controls_el_stop_label)
        self.controls_el_stop_text = QtWidgets.QLineEdit(text="1.0")
        # self.controls_el_stop_text.setSizeHint()
        self.controls_el_stop_layout.addWidget(self.controls_el_stop_text)
        self.controls_el_step_layout = QtWidgets.QHBoxLayout(self.controls_el_step_frame)
        self.controls_el_step_label = QtWidgets.QLabel("Step")
        self.controls_el_step_layout.addWidget(self.controls_el_step_label)
        self.controls_el_step_text = QtWidgets.QLineEdit(text="1.0")
        self.controls_el_step_layout.addWidget(self.controls_el_step_text)

        self.controls_sweepType_group = QtWidgets.QGroupBox("Sweep Type")
        self.controls_layout.addWidget(self.controls_sweepType_group)
        self.controls_sweepType_layout = QtWidgets.QVBoxLayout(self.controls_sweepType_group)
        self.controls_sweepType_serpentine = QtWidgets.QRadioButton("Serpentine")
        self.controls_sweepType_serpentine.setChecked(True)
        self.controls_sweepType_grid = QtWidgets.QRadioButton("Grid")
        self.controls_sweepType_layout.addWidget(self.controls_sweepType_serpentine)
        self.controls_sweepType_layout.addWidget(self.controls_sweepType_grid)


        self.controls_startButton = QtWidgets.QPushButton("Start Sweep")
        self.controls_layout.addWidget(self.controls_startButton)


        self.manual_up = QtWidgets.QPushButton("Up", self.manual_group)
        self.manual_down = QtWidgets.QPushButton("Down", self.manual_group)
        self.manual_left = QtWidgets.QPushButton("Left", self.manual_group)
        self.manual_right = QtWidgets.QPushButton("Right", self.manual_group)
        self.manual_step_frame = QtWidgets.QFrame(self.manual_group)
        self.manual_step_layout = QtWidgets.QHBoxLayout(self.manual_step_frame)
        self.manual_step_label = QtWidgets.QLabel("Step Size:")
        self.manual_step_layout.addWidget(self.manual_step_label)
        self.manual_step_text = QtWidgets.QLineEdit(text="0.1")
        self.manual_step_layout.addWidget(self.manual_step_text)
        
        self.manual_antSelect_group = QtWidgets.QGroupBox("Antenna", self.manual_group)
        self.manual_antSelect_layout = QtWidgets.QVBoxLayout(self.manual_antSelect_group)
        self.manual_antSelect_tx = QtWidgets.QRadioButton("Transmitter")
        self.manual_antSelect_tx.setChecked(True)
        self.manual_antSelect_rx = QtWidgets.QRadioButton("Receiver")
        self.manual_antSelect_layout.addWidget(self.manual_antSelect_tx)
        self.manual_antSelect_layout.addWidget(self.manual_antSelect_rx)

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

        # self.tx_ant = QtNetwork.QAbstractSocket(QtNetwork.QAbstractSocket.SocketType.UnknownSocketType, self)
        self.tx_ant = QtNetwork.QTcpSocket()
        self.tx_ant.connectToHost("192.168.27.194", 12345)
        self.tx_ant.connected.connect(self.connectedToServer_tx)
        self.tx_ant.errorOccurred.connect(self.failedToConnect)
        self.rx_ant = QtNetwork.QTcpSocket()
        self.rx_ant.connectToHost("192.168.27.154", 12345)
        self.rx_ant.connected.connect(self.connectedToServer_rx)
        self.rx_ant.errorOccurred.connect(self.failedToConnect)

        # Plotting
        self.plot_layout = QtWidgets.QVBoxLayout(self.plot_group)
        self.plot_static = FigureCanvas(Figure())
        self.plot_layout.addWidget(self.plot_static)
        self.plot_ax = self.plot_static.figure.subplots(subplot_kw={"projection": "3d"})
        randX = np.zeros((21, 21))
        randX[:] = np.linspace(-5, 5, 21)
        randY = np.zeros((21, 21))
        randY[:] = np.linspace(-5, 5, 21)
        # randZ = np.random.random(np.shape(randX)) * 10
        randZ = -1 * np.sqrt(np.power(randX, 2.0) + np.power(randY, 2.0))
        self.surf_plot = self.plot_ax.plot_surface(randX, randY.T, randZ, cmap = cm.coolwarm)
        self.plot_ax.set_xlabel("Azimuth")
        self.plot_ax.set_ylabel("Elevation")
        self.plot_ax.view_init(azim=0,elev=90)

        # Plot Controls
        self.plot_controls_group = QtWidgets.QGroupBox("Plot Controls")
        self.plot_layout.addWidget(self.plot_controls_group)
        self.plot_controls_save = QtWidgets.QPushButton("Save", self.plot_controls_group)

        # CONNECTIONS
        # self.controls_startButton.clicked.connect(self.start_btn_clicked)
        self.controls_startButton.clicked.connect(self.start_btn_clicked)
        self.manual_up.clicked.connect(self.up_btn_clicked)
        self.manual_left.clicked.connect(self.left_btn_clicked)
        self.manual_right.clicked.connect(self.right_btn_clicked)
        self.manual_down.clicked.connect(self.down_btn_clicked)
        self.plot_controls_save.clicked.connect(self.save_plot)

    
    def paintEvent(self, event):
        self.controls_group.setFixedSize(self.width() / 3, 3 * self.height() / 4)
        self.plot_group.setFixedSize(2 * self.width() / 5, self.height())
        self.plot_group.move(self.width()/3, 0)
        self.manual_group.setFixedSize(self.width() / 3, self.height()/4)
        self.manual_group.move(0, 3*self.height()/4)

        #Layout the Manual Group
        self.manual_left.setFixedWidth(self.manual_right.width())
        self.manual_down.setFixedWidth(self.manual_right.width())
        self.manual_up.setFixedWidth(self.manual_right.width())

        self.manual_up.move(int(self.manual_group.width()/2 - self.manual_up.width()/2), 20)
        self.manual_left.move(self.manual_up.x() - self.manual_left.width(), self.manual_up.y() + self.manual_up.height())
        self.manual_right.move(self.manual_up.x() + self.manual_left.width(), self.manual_up.y() + self.manual_up.height())
        self.manual_down.move(self.manual_up.x(), self.manual_up.y() + 2 * self.manual_up.height())

        self.manual_antSelect_group.move(0, self.manual_down.y() + self.manual_down.height())

        self.manual_step_frame.move(self.manual_antSelect_group.width(), self.manual_antSelect_group.y())

        self.info_group.setFixedSize(self.width() - self.plot_group.x() - self.plot_group.width(), self.height())
        self.info_group.move(self.width() - self.info_group.width(), 0)

        self.plot_controls_save.move(20, 20)


        return super().paintEvent(event)

    @QtCore.Slot(float, float, float, float, float, float, str)
    def startMeasurement(self, el_start, el_stop, el_step, az_start, az_stop, az_step, measType, antenna, point_order):
        print(f"Starting measurement! THIS IS IN MAIN!!!")
        self.ant_sock = None
        if antenna == "receiver":
            self.ant_sock = self.rx_ant
        else:
            self.ant_sock = self.tx_ant
        self.ant_sock.readyRead.connect(self.on_tcp_data)
        self.sweepController = sweepControl(el_start, el_stop, el_step, az_start, az_stop, az_step, point_order=point_order)
        self.sweepController.send_command.connect(self.send_cmd)
        self.responseRecv.connect(self.sweepController.on_res_received)
        self.sweepController.new_location.connect(self.on_new_location)
        self.sweepController.new_az.connect(self.on_new_az)
        self.sweepController.new_el.connect(self.on_new_el)
        self.sweepController.point_finished.connect(self.on_point_finished)
        self.measType = measType
        self.measAnt = antenna
        self.sweepController.measurement_finished.connect(self.onNewData)
        # self.sweepController.finished.connect(self.sweepController.deleteLater)
        self.sweepController.sweepFinished.connect(self.on_sweep_finished)
        print(f"Running Thread")
        # self.sweep_thread.start()
        self.sweepController.start()
        print(f"Thread Ran")

    @QtCore.Slot()
    def connectedToServer_rx(self):
        print(f"Connected to RX server!")
    @QtCore.Slot()
    def connectedToServer_tx(self):
        print(f"Connected to TX server!")
    @QtCore.Slot()
    def failedToConnect(self, err):
        print(f"Connection to server failed!\n\t{err}")

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
    def on_point_finished(self, idx):
        self.info_idx_label.setText(f"Point Index: {idx}")

    @QtCore.Slot()
    def start_btn_clicked(self):
        # print(f"Start Clicked!")

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

        # print(f"Starting Test:")
        # print(f"\tType: {measType}")
        # print(f"\tSweeping: {antSweeping}")
        # print(f"\tAzimuth")
        # print(f"\t\tStart: {az_start}")
        # print(f"\t\tStop: {az_stop}")
        # print(f"\t\tStep: {az_step}")
        # print(f"\tElevation")
        # print(f"\t\tStart: {el_start}")
        # print(f"\t\tStop: {el_stop}")
        # print(f"\t\tStep: {el_step}")

        self.startMeasurement(el_start, el_stop, el_step, az_start, az_stop, az_step, measType, antSweeping, sweeptype)
    
    @QtCore.Slot()
    def up_btn_clicked(self):
        # print(f"Up Clicked!")
        ant = "transmitter" if self.manual_antSelect_tx.isChecked() else "receiver"
        step = float(self.manual_step_text.text())
        # print(f"{ant} up {step} degrees")
        if ant == "transmitter":
            self.ant_sock = self.tx_ant
            self.ant_sock.readyRead.connect(self.on_tcp_data)
            self.tx_ant.write(f'move_el_DM542T.py:{step}'.encode())
        else:
            self.ant_sock = self.rx_ant
            self.ant_sock.readyRead.connect(self.on_tcp_data)
            self.rx_ant.write(f'move_el_DM542T.py:{step}'.encode())
    
    @QtCore.Slot()
    def down_btn_clicked(self):
        # print(f"Down Clicked!")
        ant = "transmitter" if self.manual_antSelect_tx.isChecked() else "receiver"
        step = float(self.manual_step_text.text())
        # print(f"{ant} down {step} degrees")
        if ant == "transmitter":
            self.tx_ant.write(f'move_el_DM542T.py:{-1 * step}'.encode())
        else:
            self.rx_ant.write(f'move_el_DM542T.py:{-1 * step}'.encode())
    
    @QtCore.Slot()
    def left_btn_clicked(self):
        # print(f"Left Clicked!")
        ant = "transmitter" if self.manual_antSelect_tx.isChecked() else "receiver"
        step = float(self.manual_step_text.text())
        print(f"{ant} left {step} degrees")
        if ant == "transmitter":
            self.tx_ant.write(f'move_az_DM542T.py:{-1 * step}'.encode())
        else:
            self.rx_ant.write(f'move_az_DM542T.py:{-1 * step}'.encode())
    
    @QtCore.Slot()
    def right_btn_clicked(self):
        # print(f"Right Clicked!")
        ant = "transmitter" if self.manual_antSelect_tx.isChecked() else "receiver"
        step = float(self.manual_step_text.text())
        print(f"{ant} right {step} degrees")
        if ant == "transmitter":
            self.tx_ant.write(f'move_az_DM542T.py:{step}'.encode())
        else:
            self.rx_ant.write(f'move_az_DM542T.py:{step}'.encode())
    
    @QtCore.Slot()
    def onNewData(self):
        if self.surf_plot is None:
            self.surf_plot = self.plot_ax.plot_surface(self.sweepController.az_angle, self.sweepController.el_angle, self.sweepController.peak_val, cmap = cm.coolwarm)
        else:

            az_angle = self.sweepController.grid.get_az_angle_grid()
            el_angle = self.sweepController.grid.get_el_angle_grid()
            peak_val = self.sweepController.grid.get_peak_val_grid()
            # print(f"PLOT: AZ_ANGLE_GRID: {az_angle}")

            # self.plot_ax.cla()
            self.surf_plot.remove()
            self.surf_plot = self.plot_ax.plot_surface(az_angle, el_angle, peak_val, cmap = cm.coolwarm)
            self.plot_static.draw()
            # self.surf_plot.set_data(self.sweepController.az_angle, self.sweepController.el_angle, self.sweepController.peak_val)

    @QtCore.Slot()
    def save_plot(self):
        if self.sweepController is None:
            print(f"ERROR: No sweep data to save. You're looking at the demo!")
            return
        print(f"Saving plot")
        fd = QtWidgets.QFileDialog.getSaveFileName(self,filter="Matlab Files (*.mat)")

        print(f"File Destination: {fd}")

        if fd[0] != "":

            mdict = {
                'peak_val': self.sweepController.grid.get_peak_val_grid(),
                'peak_freq': self.sweepController.grid.get_peak_freq_grid(),
                'az_angle': self.sweepController.grid.get_az_angle_grid(),
                'el_angle': self.sweepController.grid.get_el_angle_grid(),
                'point_idx': self.sweepController.grid.get_idx_grid()
            }

            scipy.io.savemat(f"{fd[0]}", mdict)

    @QtCore.Slot(float, float)
    def update_loc(az, el):
        print(f"New Location:\n\tAz: {az}\n\tEl: {el}")

    @QtCore.Slot(str)
    def send_cmd(self, cmd):
        # if self.ant_sock.bytesAvailable() > 0:
        #     _ = self.ant_sock.readAll()
        # print(f"Sending Command {cmd}")
        if self.ant_sock.bytesAvailable:
            self.ant_sock.readAll()
        self.ant_sock.write(cmd.encode())
        self.ant_sock.flush()

    # OLD    
    # @QtCore.Slot()
    # def on_tcp_data(self):
    #     res = self.ant_sock.read(1024)
    #     if res.isNull():
    #         return False, None

    #     res_str = res.data().decode()
    #     # print(f"res_str: {res_str}")
        
    #     cmd_arg_split = res_str.split(":")
    #     cmd_succ = cmd_arg_split[0].split("_")[1] == "succ"
    #     cmd_plane = cmd_arg_split[1]
    #     cmd_angle = cmd_arg_split[2]
    #     if cmd_succ:
    #         self.responseRecv.emit(cmd_succ, cmd_plane, float(cmd_angle))
    #     else:
    #         self.responseRecv.emit(cmd_succ, None, None)
    @QtCore.Slot()
    def on_tcp_data(self):
        res = self.ant_sock.read(1024)
        if res.isNull():
            return False, None
        
        res_str = res.data().decode()

        data = json.loads(res_str)

        print(f"Received data: {data}")

        
        


    @QtCore.Slot()
    def on_sweep_finished(self):
        print(f"SAVE_PLOT IN ON_SWEEP_FINISHED")
        self.save_plot()

if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = MainWindow()
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())