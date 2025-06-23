import numpy as np
from PySide6 import QtCore, QtWidgets, QtGui, QtNetwork
import time
import scipy
import points

import pyvisa
from twister_api.oscilloscope_interface import Oscilloscope
from logger import logger




class sweepControl(QtCore.QThread):
    nextPoint = QtCore.Signal(int)
    newSweep = QtCore.Signal(int) # (number of points)
    newLocation = QtCore.Signal(float, float)
    sweepFinished = QtCore.Signal()
    send_command = QtCore.Signal(str)
    movement_complete = QtCore.Signal()
    target_reached = QtCore.Signal()
    ready_measure = QtCore.Signal()
    measurement_finished = QtCore.Signal()
    point_finished = QtCore.Signal(int)
    new_location = QtCore.Signal(float, float)
    new_az = QtCore.Signal(float)
    new_el = QtCore.Signal(float)

    def __init__(self, el_start_angle, el_end_angle, el_step_size, az_start_angle, az_end_angle, az_step_size, waveform=False, settling_time=0.2, point_order="serpentine"):
        super().__init__()
        self.sweep_log = logger("sweep_log.txt")
        self.sweep_log.info(f"Initializing sweep")
        self.res_recv = False
        self.paused = False
        self.active = False
        self.move_queue = []
        self.target_point = None
        self.current_point = None
        self.point_index = 0
        self.needs_measured = False
        self.isFinished = False

        self.waveform = waveform
        self.point_order = point_order

        self.az_start_angle = az_start_angle
        self.az_end_angle = az_end_angle
        self.az_step_size = az_step_size
        self.el_start_angle = el_start_angle
        self.el_end_angle = el_end_angle
        self.el_step_size = el_step_size
        # self.ant_sock = ant_sock
        self.settling_time = settling_time
        
        self.save_folder = "C:/Users/UTOL/Desktop/"
        self.save_name = "test"

        

        # el_sweep_size = el_end_angle - el_start_angle
        # az_sweep_size = az_end_angle - az_start_angle
        # self.az_values = int(round(az_sweep_size/az_step_size)) + 1
        # self.el_values = int(round(el_sweep_size/el_step_size)) + 1

        # self.zero_grid = np.zeros((self.el_values, self.az_values))
        # self.peak_val = np.zeros((self.el_values, self.az_values)) * np.NaN
        # self.az_angle = np.zeros((self.el_values, self.az_values))
        # self.el_angle = np.zeros((self.el_values, self.az_values))
        # self.peak_freq = np.zeros((self.el_values, self.az_values))

        self.grid = points.Grid(el_start_angle, el_end_angle, el_step_size, az_start_angle, az_end_angle, az_step_size)
        self.sweep_log.debug(self.grid.get_az_angle_grid())
        self.sweep_log.debug(self.grid.get_el_angle_grid())
        self.rm = pyvisa.ResourceManager()
        self.Infiniium = self.rm.open_resource("TCPIP0::192.168.27.10::inst0::INSTR")
        self.Infiniium.timeout = 20000
        self.Infiniium.clear()
        self.scope = Oscilloscope(
            visa_address="TCPIP0::192.168.27.10::inst0::INSTR", debug=True)

        # return zero_grid, peak_val, peak_freq, az_angle, el_angle
        self.sweep_log.info(f"Sweep Initialized:")
        self.sweep_log.info(f"\tAzimuth:")
        self.sweep_log.info(f"\t\tStart: {az_start_angle}")
        self.sweep_log.info(f"\t\tStop: {az_end_angle}")
        self.sweep_log.info(f"\t\tStep: {az_step_size}")
        self.sweep_log.info(f"\tElevation:")
        self.sweep_log.info(f"\t\tStart: {el_start_angle}")
        self.sweep_log.info(f"\t\tStop: {el_end_angle}")
        self.sweep_log.info(f"\t\tStep: {el_step_size}")

        # self.ready_measure.connect(self.measure)
        self.measurement_finished.connect(self.next)
        self.target_reached.connect(self.on_arrived)

    def _send_command(self, command):
        self.res_recv = False
        self.send_command.emit(command)
        self.sweep_log.debug(f"SENT CMD: {command}")
        
    def wait_for_response(self):
        while self.res_recv == False:
            continue

    def measure(self):
        time.sleep(self.settling_time)
        
        if self.waveform:
            self.Infiniium.write(":DIGitize")
            time_values, voltage_values, y_origin, x_increment = self.get_waveform(1)
            filename = f"waveform_az{self.current_point.az}_el{self.current_point.el_ideal}.mat"
            scipy.io.savemat(f"{self.save_folder}{filename}.mat",
                            {'time': time_values, 'voltage': voltage_values, 'y_org': y_origin, 'x_inc': x_increment})
            
        else:
            # Get the FFT Peak
            peakPWR_temp = self.scope.get_fft_peak(2)
            peak_freq_temp = self.scope.do_query(f":FUNCtion2:FFT:PEAK:FREQ?")
            
            peak_val = peakPWR_temp
            peak_freq = peak_freq_temp.strip('""')
            
            
            self.current_point.addReading(peak_val, peak_freq)
        self.sweep_log.debug(f"Measurement complete at point {self.point_index}")
        self.needs_measured = False
        self.measurement_finished.emit()
    
    def return_to_start(self):
        self.move_to_point(points.Point(0, 0))
    
    def run(self): #This is for the threading
        self.runSweep(False)

    def runSweep(self, waveform=False):
        # Create a cmd timeout timer. If the cmd is sent and there is no response for 30 seconds, resend cmd
        self.cmd_timer = QtCore.QTimer()
        self.cmd_timer.setSingleShot(True)
        self.cmd_timer.setInterval(50)
        self.cmd_timer.timeout.connect(self.on_cmd_timeout)

        # self._send_command("set_home:0")
        self._send_command("set_home:0") # Emitting the signal directly to skip waiting for a response
        self.az_current_angle = 0
        self.el_current_angle = 0
        self.waveform = waveform
        self.wait_for_response()
        # self.move_to_start()
        self.active = True
        self.next()
        # self.move_to_point(self.grid.get_point_by_travel_order(0))
        self.exec()
    def exec(self):
        while self.active:
            # time.sleep(1)
            continue
        # self.
        # self.exit()

    def get_waveform(self, channel):
        self.Infiniium.write(f":WAVeform:SOURce CHANnel{channel}")
        self.Infiniium.write(":WAVeform:FORMat BYTE")
        self.Infiniium.write(":WAVeform:STReaming OFF")

        x_increment = float(self.Infiniium.query(":WAVeform:XINCrement?"))
        x_origin = float(self.Infiniium.query(":WAVeform:XORigin?"))
        y_increment = float(self.Infiniium.query(":WAVeform:YINCrement?"))
        y_origin = float(self.Infiniium.query(":WAVeform:YORigin?"))

        preamble = self.Infiniium.query(":WAVeform:PREamble?").split(',')
        num_points = int(preamble[2])

        raw_data = self.scope.get_waveform_words([1])

        time_values = np.linspace(
            x_origin, x_origin + x_increment * (num_points - 1), num_points)
        voltage_values = (raw_data * y_increment) + y_origin

        return time_values, voltage_values, y_origin, x_increment

    
    def next(self):
        self.sweep_log.debug(f"NEXT DEBUG:")
        self.sweep_log.debug(f"\tPoint idx: {self.point_index}")
        self.sweep_log.debug(f"\tActive: {self.active}")
        self.sweep_log.debug(f"\t\tPaused: {self.paused}")
        self.sweep_log.debug(f"\t\tNo target no point: {self.target_point is None and self.current_point is None}")
        self.sweep_log.debug(f"\t\tTarget Point not None: {self.target_point is not None}")
        self.sweep_log.debug(f"\t\tNeeds Measured: {self.needs_measured}")
        if self.active == True: # If actively testing
            if self.paused: # If paused
                pass
            elif self.target_point is None and self.current_point is None: # If no target and no current point, then we haven't started the test yet
                if self.point_order == "serpentine":
                    self.move_to_point(self.grid.get_point_by_travel_order(0))
                elif self.point_order == "grid":
                    self.move_to_point(self.grid.get_point_by_grid_order(0))

            elif self.target_point is not None: # If there is a target point and we somehow made it here...
                if len(self.move_queue) == 0: # If no movement was queued for this point
                    self.sweep_log.warn(f"Unqueued movement. Queuing(?)...")
                    self.move_to_point(self.target_point)
                elif self.target_point.az == self.az_current_angle and self.target_point.el == self.el_current_angle: # If we are already at the point and somehow got here
                    self.move_queue.pop()
                    self.move_queue.pop()
                    self.on_arrived()
            elif self.needs_measured: #If we are at a point that needs to be measured
                self.measure()            
            else: # Otherwise, we've finished a point
                self.point_finished.emit(self.point_index)
                self.current_point = None
                self.point_index += 1
                if (self.point_index == self.grid.get_serpentine().size): # If our next index is not in our range
                    self.sweep_log.info(f"Sweep complete!")
                    self.move_to_point(points.Point(0, 0))
                    # self.finished.emit()
                    self.active = False
                else: # Otherwise, it is in our range
                    if self.point_order == "serpentine":
                        self.move_to_point(self.grid.get_point_by_travel_order(self.point_index))
                    elif self.point_order == "grid":
                        self.move_to_point(self.grid.get_point_by_grid_order(self.point_index))
    
    def move_to_point(self, point: points.Point):
        self.needs_measured = False
        self.target_point = point
        self.target_point.idx = self.point_index
        az_step = point.az - self.az_current_angle
        self.move_queue.append(f"move_az_DM542T.py:{az_step}")
        self.move_queue.append(f'move_el_DM542T_absolute.py:{point.el_ideal}')
        self._send_command(self.move_queue[0])
    
    @QtCore.Slot(bool, str, float)
    def on_res_received(self, succ, cmd, data):
        self.res_succ = succ
        self.res_data = data
        self.res_recv = True

        if len(self.move_queue) > 0:
            if cmd == "home": # If the response was to a receive command
                pass
            elif cmd == "az" or cmd == "el": # If the response was to either azimuth or elevation commands
                if cmd == "az" and self.move_queue[0].find("az") > 0: # If the response was azimuth and we sent azimuth
                    self.move_queue.pop(0)
                    self.az_current_angle = data
                    self.new_az.emit(data)
                    # Nothing else to do...
                elif cmd == "el" and self.move_queue[0].find("el") > 0:
                    self.move_queue.pop(0)
                    self.new_el.emit(data)
                    self.target_point.set_el(self.res_data)

                if len(self.move_queue) == 0:
                    self.target_reached.emit()
                    # self.on_target_reached()
                else:
                    self._send_command(self.move_queue[0])


        self.sweep_log.debug(f"ON_RES_RECV: {self.res_data}")

    @QtCore.Slot()
    def on_home_set(self):
        self.res_recv = True

    @QtCore.Slot()
    def on_target_reached(self):
        self.current_point = self.target_point
        self.target_point = None
        self.needs_measured = True
        self.next()

    @QtCore.Slot()
    def on_toggle_pause(self):
        if not self.paused:
            self.paused = True
        else:
            self.paused = False
            self.next()
    
    @QtCore.Slot()
    def on_stop(self):
        self.active = False
        self.move_to_point(points.Point(0, 0))

    @QtCore.Slot()
    def on_measurement_finished(self):
        if not self.paused:
            self.nextPoint.emit(self.point_index)
        else:
            pass

    @QtCore.Slot()
    def on_arrived(self):
        self.sweep_log.debug(f"Arrived @ {self.point_index}/{len(self.move_queue)}")
        self.current_point = self.target_point
        self.target_point = None
        if self.active:
            self.new_location.emit(self.current_point.az, self.current_point.el)
            self.ready_measure.emit()
            self.needs_measured = True
        else:
            self.sweep_log.debug(f"No longer active. Must be finished!")
            if not self.isFinished:
                self.isFinished = True
                self.sweepFinished.emit()

        
        self.next()

    @QtCore.Slot()
    def on_cmd_timeout(self):
        self.sweep_log.warn("Command Timed out! Resending...")
        self._send_command(self.move_queue[0])

