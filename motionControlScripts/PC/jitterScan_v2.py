""" 
This script looks for left/right and up/down key presses to adjust the stages
"""

import socket
import msvcrt # Detects key input w/o pressing enter
import time
import sys
from twister_api.oscilloscope_interface import Oscilloscope
#from twister_api.waveformgen_interface import WaveformGenerator
#from twister_api.signalgen_interface import SignalGenerator
import twister_api.twister_utils as twister_utils
import twister_api.fileio as fileio
import scipy

# Program parameters
az_sweep_start = float(sys.argv[1])
az_sweep_end = float(sys.argv[2])
az_sweep_step = float(sys.argv[3])
save_name = str(sys.argv[4])
settling_time = 1 # Time allowed for settling/averaging between measurements
#save_folder = 'C:/Users/Ethan Abele/OneDrive - Oklahoma A and M System/THz Jitter/measurements_29April2024/AzElSweep/'
save_folder = 'C:/Users/Ethan Abele/OneDrive - Oklahoma A and M System/Research/THz Jitter/python_scripts/tests_6Feb2025/'
#save_name = 'Az_sweep_El_000'


#save_name = 'Cassegrain_sweep_041.mat'
save_path = save_folder+save_name+'.mat'

# Setup instrument
scope = Oscilloscope(visa_address="TCPIP0::192.168.27.10::inst0::INSTR",debug=True)
#scope = Oscilloscope(visa_address="TCPIP0::10.10.10.10::inst0::INSTR",debug=True)


# Pi server comm settings
HOST = '192.168.27.194'  # Raspberry Pi's IP address
PORT = 12345       # The port on which the server is listening

# Function to send motion requests to raspberry pi server. MRIserver.py must be running in the pi
def send_command(command):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(command.encode())
        

# Request current stage pos from user
az_pos = float(input("Enter the current Azimuth stage position and press Enter: "))
el_pos = float(input("Enter the current Elevation angle and press Enter: "))


# First move stage to start position
print("Moving Az stage into position")
motion = az_sweep_start-az_pos
send_command(f'move_az_DM542T.py:{motion}')
time.sleep(13)
az_pos = az_sweep_start
print(["Starting sweep at Az pos = ", az_pos]) 

peak_val = []
az_angle = []
peak_freq = []
while az_pos <= az_sweep_end:
    # Give some time for averaging/settling
    time.sleep(settling_time)
    
    # Get the FFT Peak
    peakPWR_temp = scope.get_fft_peak(2)
    peak_freq_temp = scope.do_query(f":FUNCtion2:FFT:PEAK:FREQ?")
    peak_val.append(peakPWR_temp)
    peak_freq.append(peak_freq_temp)
    #peak_val.append(999)
    az_angle.append(az_pos)
    
    print(f"Stage position = {az_pos}, Peak freq = {peak_freq_temp} Hz, Peak Pwr = {peakPWR_temp} dBm")
    
    if az_pos < az_sweep_end:
        # Move stage to next position
        send_command(f'move_az_DM542T.py:{az_sweep_step}') # Example of how to run a script on the pi
        az_pos = round(az_pos+az_sweep_step,3)
    else:
        break
    
    
        
# Convert into matlab readable format and save
mdict = {"az_angle":az_angle,"el_angle":el_pos,"FFT_peak":peak_val, "peak_freq":peak_freq}
scipy.io.savemat(save_path,mdict)  

print("Sweep Complete")
#print(["Az pos = ", az_pos]) 
