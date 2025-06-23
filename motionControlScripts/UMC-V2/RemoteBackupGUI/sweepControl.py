import numpy as np
from PySide6 import QtCore, QtWidgets, QtGui, QtNetwork
import time
import scipy

import pyvisa
from twister_api.oscilloscope_interface import Oscilloscope

class sweepControl(QtCore.QThread):
    newPoint = QtCore.Signal()
    newSweep = QtCore.Signal(int) # (number of points)
    newLocation = QtCore.Signal(float, float)
    finished = QtCore.Signal()
    send_command = QtCore.Signal(str)
    def __init__(self, el_start_angle, el_end_angle, el_step_size, az_start_angle, az_end_angle, az_step_size, settling_time=0.001):
        super().__init__()
        print(f"Initializing sweep")
        self.res_recv = False

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

        el_sweep_size = el_end_angle - el_start_angle
        az_sweep_size = az_end_angle - az_start_angle
        self.az_values = int(round(az_sweep_size/az_step_size)) + 1
        self.el_values = int(round(el_sweep_size/el_step_size)) + 1

        self.zero_grid = np.zeros((self.el_values, self.az_values))
        self.peak_val = np.zeros((self.el_values, self.az_values)) * np.NaN
        self.az_angle = np.zeros((self.el_values, self.az_values))
        self.el_angle = np.zeros((self.el_values, self.az_values))
        self.peak_freq = np.zeros((self.el_values, self.az_values))

        self.rm = pyvisa.ResourceManager()
        self.Infiniium = self.rm.open_resource("TCPIP0::192.168.27.10::inst0::INSTR")
        self.Infiniium.timeout = 20000
        self.Infiniium.clear()
        self.scope = Oscilloscope(
            visa_address="TCPIP0::192.168.27.10::inst0::INSTR", debug=True)

        # return zero_grid, peak_val, peak_freq, az_angle, el_angle
        print(f"Sweep Initialized:")
        print(f"\tAzimuth:")
        print(f"\t\tStart: {az_start_angle}")
        print(f"\t\tStop: {az_end_angle}")
        print(f"\t\tStep: {az_step_size}")
        print(f"\tElevation:")
        print(f"\t\tStart: {el_start_angle}")
        print(f"\t\tStop: {el_end_angle}")
        print(f"\t\tStep: {el_step_size}")
        # print(f"\tPoints:")
        # print(f"")

    def _send_command(self, command):
        self.res_recv = False
        self.send_command.emit(command)
        self.wait_for_response()
        print(f"Done Waiting: {self.res_data}")
        return self.res_succ, self.res_data
        # with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # self.ant_sock.write(command.encode())
        # self.ant_sock.flush()
        # self.ant_sock.waitForReadyRead()
        # res = self.ant_sock.read(1024)
        # if res.isNull():
        #     return False, None

        # res_str = res.data().decode()
        # print(f"res_str: {res_str}")
           
        # cmd_succ = res_str.split("_")[1] == "succ"
        # if cmd_succ and res_str.find("el") > 0:
        #     return True, float(res_str.split(":")[1])
        # else:
        #     return cmd_succ, None
        
    def wait_for_response(self):
        while self.res_recv == False:
            # print(f"WAITING")
            continue
    
    def take_measurement(self, i, j, az_pos, el_pos, waveform, callback=None):
        print(f"Taking Measurement...")
        time.sleep(self.settling_time)

        az_pos = round(az_pos, 2)
        el_pos = round(el_pos, 2)

        if waveform:
            self.Infiniium.write(":DIGitize")
            time_values, voltage_values, y_origin, x_increment = self.get_waveform(1)
            filename = f"waveform_az{az_pos}_el{el_pos}.mat"
            scipy.io.savemat(f"{self.save_folder}{filename}.mat",
                            {'time': time_values, 'voltage': voltage_values, 'y_org': y_origin, 'x_inc': x_increment})
        else:
            # Get the FFT Peak
            peakPWR_temp = self.scope.get_fft_peak(2)
            peak_freq_temp = self.scope.do_query(f":FUNCtion2:FFT:PEAK:FREQ?")
            self.peak_val[i][j] = peakPWR_temp
            self.peak_freq[i][j] = peak_freq_temp.strip('""')
            self.az_angle[i][j] = az_pos
            self.el_angle[i][j] = el_pos
            
            # if callback is not None:
            #     callback(az_pos, el_pos, self.peak_freq[i][j], peakPWR_temp)
            self.newPoint.emit()

        

    def move_to_start(self):
        # We know that the controller should be at 0 in both elevation and azimuth to start
        # Move azimuth to start location
        print("Moving to:")
        print("Azimuth: ", self.az_start_angle)
        print("Elevation: ", self.el_start_angle)
        self.send_command.emit(f'move_az_DM542T.py:{self.az_start_angle}')
        self.wait_for_response()
        az_succ = self.res_succ
        # time.sleep(abs(az_start_angle * az_delay/.1))
        el_succ, angle = self._send_command(f'move_el_DM542T_absolute.py:{self.el_start_angle}')
        # time.sleep(abs(el_start_angle * el_delay/.1))
        self.az_current_angle = self.az_start_angle
        self.el_current_angle = angle

        return (az_succ and el_succ) # Return's success of homing event
    
    def return_to_start(self):
        # We know that the controller should be at 0 in both elevation and azimuth to start
        # Move azimuth to start location
        print("Moving to:")
        print("Azimuth: 0")
        print("Elevation: 0")
        self.send_command.emit(f'move_az_DM542T.py:{-1*self.az_current_angle}')
        self.wait_for_response()
        az_succ = self.res_succ
        # time.sleep(abs(az_start_angle * az_delay/.1))
        el_succ, _ = self._send_command(f'move_el_DM542T_absolute.py:{0}')
        # time.sleep(abs(el_start_angle * el_delay/.1))
        self.az_current_angle = 0
        self.el_current_angle = 0

        return (az_succ and el_succ) # Return's success of homing event
    
    def run(self): #This is for the threading
        self.runSweep(False)

    def runSweep(self, waveform=False):
        print(f"Setting current position as home")
        # self._send_command("set_home:0")
        # self.send_command.emit("set_home:0") # Emitting the signal directly to skip waiting for a response
        print(f"Moving to start!")
        self.move_to_start()
        print(f"Running Sweep!")
        self.waveform = waveform
        self.sweep_2D(self.zero_grid)
        
        self.az_angle[1::2] = self.az_angle[1::2, ::-1]
        self.peak_freq[1::2] = self.peak_freq[1::2, ::-1]
        self.peak_val[1::2] = self.peak_val[1::2, ::-1]

        if not waveform:
            mdict = {
                'peak_val': self.peak_val,
                'peak_freq': self.peak_freq,
                'az_angle': self.az_angle,
                'el_angle': self.el_angle
            }
            scipy.io.savemat(f"{self.save_folder}{self.save_name}.mat", mdict)
        
        self.return_to_start() # Should be called return to 0
        self.finished.emit()

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

        # raw_data = Infiniium.query_binary_values(
        #     ":WAVeform:DATA?", datatype='b', container=np.array)

        raw_data = self.scope.get_waveform_words([1])

        time_values = np.linspace(
            x_origin, x_origin + x_increment * (num_points - 1), num_points)
        voltage_values = (raw_data * y_increment) + y_origin

        return time_values, voltage_values, y_origin, x_increment
    
    def sweep_2D(self, grid, callback=None):
        # global az_current_angle, el_current_angle, paused, waveform
        num_cols = grid.shape[1]
        num_rows = grid.shape[0]

        for i in range(num_rows):
            print("Scanning row: ", i)
            # if keyboard.is_pressed('p'):
            #     paused = True
            #     print("Sweep paused. Press 'r' to resume.")
            # if paused:
            #     wait_for_resume()
            if i % 2 == 0:
                # Travel left to right on even indexed roads
                for j in range(num_cols):
                    # if keyboard.is_pressed('p'):
                    #     paused = True
                    #     print("Sweep paused. Press 'r' to resume.")
                    # if paused:
                    #     wait_for_resume()

                    print("Current azimuth: ", round(self.az_current_angle, 2),
                        "    Current elevation: ", self.el_current_angle)
                    # time.sleep(abs(az_delay * az_step_size/.1))
                    self.take_measurement(i, j, self.az_current_angle,
                                    self.el_current_angle, self.waveform, callback=callback)
                    # time.sleep(settling_time)
                    if (j != num_cols - 1): # If we aren't in the last position
                        move_succ, _ = self._send_command(f'move_az_DM542T.py:{self.az_step_size}')
                        self.az_current_angle += self.az_step_size
                    if not move_succ:
                        print("*"*30)
                        print(f"ERROR! MOVEMENT FAILED!")
                        print(f"\tAzimuth {self.az_step_size}")

            else:
                # Travel right to left on odd indexed roads
                for j in range(num_cols):
                    # if keyboard.is_pressed('p'):
                    #     paused = True
                    #     print("Sweep paused. Press 'r' to resume.")
                    # if paused:
                    #     wait_for_resume()
                    print("Current azimuth: ", round(self.az_current_angle, 2),
                        "    Current elevation: ", self.el_current_angle)
                    # time.sleep(abs(az_delay * az_step_size/.1))
                    self.take_measurement(i, j, self.az_current_angle,
                                    self.el_current_angle, self.waveform, callback=callback)
                    if (j != num_cols - 1): # If we aren't in the last position
                        move_succ, _ = self._send_command(f'move_az_DM542T.py:{-1*self.az_step_size}')
                        self.az_current_angle -= self.az_step_size
                    if not move_succ:
                        print("*"*30)
                        print(f"ERROR! MOVEMENT FAILED!")
                        print(f"\tAzimuth {-1*self.az_step_size}")
                    # time.sleep(settling_time)
            if i != num_rows-1:
                print(f"CALLING: move_el_DM542T_absolute.py:{self.el_start_angle + (i+1)*self.el_step_size}")
                el_succ, change = self._send_command(f'move_el_DM542T_absolute.py:{self.el_start_angle + (i+1)*self.el_step_size}')
                if el_succ:
                    self.el_current_angle = self.res_data # Change is now the actual reported angle
                    print(f"NEW ELEVATION: {self.el_current_angle}\n\t{self.res_data}")
                else:
                    print(f"ERROR: NO CHANGE REPORTED!!!")
                # time.sleep(abs(el_delay * el_step_size/.1))

            # if keyboard.is_pressed('p'):
            #     paused = True
            #     print("Sweep paused. Press 'r' to resume.")

        print("Sweep complete!")
        return 0
    
    QtCore.Slot(bool, float)
    def on_res_received(self, succ, data):
        self.res_succ = succ
        self.res_data = data
        self.res_recv = True
        # print(f"ON_RES_RECV: {self.res_data}")
