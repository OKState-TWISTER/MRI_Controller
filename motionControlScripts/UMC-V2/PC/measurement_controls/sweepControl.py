import numpy as np
from PySide6 import QtCore, QtWidgets, QtGui, QtNetwork
import time
import scipy
import points

from logger import logger
import json
from devices.scopecontrol import ScopeController



class sweepControl(QtCore.QThread):
    nextPoint = QtCore.Signal(int)
    newSweep = QtCore.Signal(int) # (number of points)
    newLocation = QtCore.Signal(float, float)
    sweepFinished = QtCore.Signal()
    send_command = QtCore.Signal(dict)
    movement_complete = QtCore.Signal()
    target_reached = QtCore.Signal()
    ready_measure = QtCore.Signal()
    measurement_finished = QtCore.Signal()
    point_finished = QtCore.Signal(int)
    new_location = QtCore.Signal(float, float)
    new_az = QtCore.Signal(float)
    new_el = QtCore.Signal(float)
    scope_err = QtCore.Signal()

    def __init__(self, el_start_angle, el_end_angle, el_step_size, az_start_angle, az_end_angle, az_step_size, scope: ScopeController, waveform=False, settling_time=0.2, point_order="serpentine"):
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

        self.grid = points.Grid(el_start_angle, el_end_angle, el_step_size, az_start_angle, az_end_angle, az_step_size)
        self.sweep_log.debug(self.grid.get_az_angle_grid())
        self.sweep_log.debug(self.grid.get_el_angle_grid())
        self.scope = scope

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
        send = command
        self.send_command.emit(send)
        self.sweep_log.debug(f"SENT CMD: {command}")
        
    def wait_for_response(self):
        self.res_recv = False
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
            peak_val, peak_freq = self.scope.get_peak()
            
            
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
        cmd = {}
        cmd['timestamp'] = time.time()
        cmd['cmd'] = "set_home"
        self._send_command(cmd) # Emitting the signal directly to skip waiting for a response
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
        
        timestamp = time.time()
        # move_az = {}
        # move_az['timestamp'] = timestamp
        # move_az['cmd'] = "move"
        # move_az['args'] = {}
        # move_az['args']['pl'] = "az"
        # move_az['args']['deg'] = f"{az_step}"
        # self.move_queue.append(move_az) # self.move_queue.append(f"move_az_DM542T.py:{az_step}")
        
        # move_el = {}
        # move_el['timestamp'] = timestamp + 1 # Adding a second so that this command command "after" the az movement
        # move_el['cmd'] = "move"
        # move_el['args'] = {}
        # move_el['args']['pl'] = "el"
        # move_el['args']['relative'] = False
        # move_el['args']['deg'] = f"{point.el_ideal}"
        # self.move_queue.append(move_el) # self.move_queue.append(f'move_el_DM542T_absolute.py:{point.el_ideal}')
        
        goto_cmd = {}
        goto_cmd['timestamp'] = timestamp
        goto_cmd['cmd'] = "goto"
        goto_cmd['args'] = {}
        goto_cmd['args']['az'] = {}
        goto_cmd['args']['az']['deg'] = f"{az_step}"
        goto_cmd['args']['az']['rel'] = False
        goto_cmd['args']['el'] = {}
        goto_cmd['args']['el']['deg'] = f"{point.el_ideal}"
        goto_cmd['args']['el']['rel'] = False
        self.move_queue.append(goto_cmd)
        
        
        self._send_command(self.move_queue[0])
    
    @QtCore.Slot(bool, str, float)
    def on_res_received(self, data):
        # self.res_succ = data['res']['succ']
        self.res_recv = True
        cmd = data['cmd']

        if len(self.move_queue) > 0:
            if cmd == "home": # If the response was to a receive command
                pass
            elif cmd == "az" or cmd == "el": # If the response was to either azimuth or elevation commands
                if cmd == "az" and self.move_queue[0]['args']['pl'] == "az": # If the response was azimuth and we sent azimuth
                    self.sweep_log.debug("Azimuth response received.")
                    self.move_queue.pop(0)
                    self.az_current_angle = data['res']['ch']
                    self.new_az.emit(self.az_current_angle)
                    # Nothing else to do...
                elif cmd == "el" and self.move_queue[0]['args']['pl'] == "el":
                    self.sweep_log.debug("Elevation response received.")
                    self.move_queue.pop(0)
                    self.new_el.emit(data['res']['ch'])
                    self.target_point.set_el(data['res']['ch'])

                if len(self.move_queue) == 0:
                    self.target_reached.emit()
                    # self.on_target_reached()
                else:
                    self._send_command(self.move_queue[0])
            elif cmd == "goto" and self.move_queue[0]['cmd'] == "goto":
                self.sweep_log.debug("GOTO Response received.")
                self.move_queue.pop(0)
                self.az_current_angle = data['res']['az']['ch']
                self.new_az.emit(data['res']['az']['ch'])
                self.new_el.emit(data['res']['el']['ch'])
                self.target_reached.emit()


        # self.sweep_log.debug(f"ON_RES_RECV: {self.res_data}")

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

    @QtCore.Slot()
    def on_scope_err(self):
        self.sweep_log.debug("Scope error, returning home!")
        self.move_to_point(points.Point(0,0))

