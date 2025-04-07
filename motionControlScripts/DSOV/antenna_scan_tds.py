import pyvisa
import struct
import scipy.io
import numpy as np
import socket

# Oscilloscope connection settings
rm = pyvisa.ResourceManager()
Infiniium = rm.open_resource("TCPIP0::192.168.27.10::inst0::INSTR")
Infiniium.timeout = 20000
Infiniium.clear()

# Motion stage control settings
HOST = '192.168.27.194'  # Raspberry Pi's IP address
PORT = 12345  # Port for motion stage server

# Function to send motion requests to Raspberry Pi server
def send_command(command):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(command.encode())

# Function to retrieve waveform data from the oscilloscope
def get_waveform(channel):
    Infiniium.write(f":WAVeform:SOURce CHANnel{channel}")
    Infiniium.write(":WAVeform:FORMat BYTE")
    Infiniium.write(":WAVeform:STReaming OFF")
    
    x_increment = float(Infiniium.query(":WAVeform:XINCrement?"))
    x_origin = float(Infiniium.query(":WAVeform:XORigin?"))
    y_increment = float(Infiniium.query(":WAVeform:YINCrement?"))
    y_origin = float(Infiniium.query(":WAVeform:YORigin?"))

    preamble = Infiniium.query(":WAVeform:PREamble?").split(',')
    num_points = int(preamble[2])

    raw_data = Infiniium.query_binary_values(":WAVeform:DATA?", datatype='b', container=np.array)
    
    time_values = np.linspace(x_origin, x_origin + x_increment * (num_points - 1), num_points)
    voltage_values = (raw_data * y_increment) + y_origin

    return time_values, voltage_values

# Program parameters
az_sweep_start = float(sys.argv[1])
az_sweep_end = float(sys.argv[2])
az_sweep_step = float(sys.argv[3])
save_name = str(sys.argv[4])
settling_time = 1 # Time allowed for settling/averaging between measurements
#save_folder = 'C:/Users/Ethan Abele/OneDrive - Oklahoma A and M System/THz Jitter/measurements_29April2024/AzElSweep/'
save_folder = 'C:/Users/Ethan Abele/OneDrive - Oklahoma A and M System/Research/THz Jitter/python_scripts/tests_31Jan2025/'



save_path = save_folder+save_name+'.mat'

# Setup instrument
#scope = Oscilloscope(visa_address="TCPIP0::192.168.27.10::inst0::INSTR",debug=True)



# Request current stage pos from user
az_pos = float(input("Enter the current Azimuth stage position and press Enter: "))
el_pos = float(input("Enter the current Elevation angle and press Enter: "))


# First move stage to start position
print("Moving Az stage into position")
motion = az_sweep_start-az_pos
send_command(f'move_az_DM542T.py:{motion}')
time.sleep(10)
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
    
    # Capture the time domin waveform from Ch1
    Infiniium.write(":DIGitize")
    time_values, voltage_values = get_waveform(1)
    filename = f"waveform_az{azimuth}_el{elevation_angle}.mat"
    scipy.io.savemat(save_folder+filename, {'time': time_values, 'voltage': voltage_values})
    
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


    

Infiniium.close()
