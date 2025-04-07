# UTOL Motion Control - PC program

import socket
import socket
import keyboard  # Detects key input without pressing enter
import time
import configparser
import numpy as np
import sys
from twister_api.oscilloscope_interface import Oscilloscope
from twister_api.waveformgen_interface import WaveformGenerator
from twister_api.signalgen_interface import SignalGenerator
import twister_api.twister_utils as twister_utils
import twister_api.fileio as fileio
import scipy
import os
import datetime
import pyvisa

# Global Variables
# Azimuth
az_current_angle = 0.0
az_start_angle = 0.0
az_end_angle = 0.0
az_step_size = 0.0
AZ_MIN_STEP = 0.0
AZ_MAX_STEP = 10.0
AZ_STEP_INCREMENT = .01

# Elevation
el_current_angle = 0
el_start_angle = 0
el_end_angle = 0
el_step_size = 0
EL_MIN_STEP = 0.022
EL_MAX_STEP = 1.0
EL_STEP_INCREMENT = .022

# Tracking movement
total_movement_az = 0.0
total_movement_el = 0.0
current_key = None  # Track the currently pressed key
SEND_DELAY = 0.3
settling_time = 1  # Time allowed for settling/averaging between measurements
az_delay = 0.8  # Azimuth movement time (calibrated for a .1 degree step)
el_delay = 3  # Elevation movement time (calibrated for a .1 degree step)
paused = False

# Measurements
waveform = False

# Server
HOST = ""
PORT = 0

# Save path
save_name = str(sys.argv[1])
# save_folder = 'C:/Users/Ethan Abele/OneDrive - Oklahoma A and M System/THz Jitter/measurements_29April2024/AzElSweep/'
save_folder = 'C:/Users/Ethan Abele/OneDrive - Oklahoma A and M System/Research/THz Jitter/python_scripts/tests_22March2025/rxGainPattern/'
# save_name = 'Az_sweep_El_000'
save_path = save_folder+save_name+'.mat'

# Setup instrument
scope = Oscilloscope(
    visa_address="TCPIP0::192.168.27.10::inst0::INSTR", debug=True)
# scope = Oscilloscope(visa_address="TCPIP0::10.10.10.10::inst0::INSTR",debug=True)
rm = pyvisa.ResourceManager()
Infiniium = rm.open_resource("TCPIP0::192.168.27.10::inst0::INSTR")
Infiniium.timeout = 20000
Infiniium.clear()

# # Function to send motion requests to the Raspberry Pi server


def send_command(command):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(command.encode())


# Updates config file


def generate_config(filename="config.ini"):
    global az_current_angle, az_start_angle, az_end_angle, az_step_size, el_current_angle, el_start_angle, el_end_angle, el_step_size, HOST, PORT
    config = configparser.ConfigParser()
    today_date = datetime.datetime.now().strftime("%b. %d, %Y")

    # Define sections and key-value pairs
    config["GENERAL"] = {
        "project_name": "UTOL Motion Control",
        "version": "1.0",
        "author": "Ethan Abele / Tyler Graham",
        "date": today_date
    }

    config["SERVER"] = {
        "ip_address": "192.168.27.194",
        "port": 12346,
    }

    config["AZIMUTH CONTROL"] = {
        "current_angle": az_current_angle,
        "start_point_degrees": az_start_angle,
        "end_point_degrees": az_end_angle,
        "step_size": az_step_size
    }

    config["ELEVATION CONTROL"] = {
        "current_angle": el_current_angle,
        "start_point_degrees": el_start_angle,
        "end_point_degrees": el_end_angle,
        "step_size": el_step_size
    }

    config["MEASUREMENT TYPE"] = {
        "waveform": waveform
    }

    # Write configuration to file
    with open(filename, "w") as configfile:
        config.write(configfile)

    print(f"Configuration file '{filename}' generated successfully.")

# Reads config file and updates corresponding global variables


def read_config(filename="config.ini"):
    global az_current_angle, az_start_angle, az_end_angle, az_step_size, el_current_angle, el_start_angle, el_end_angle, el_step_size, HOST, PORT, waveform
    config = configparser.ConfigParser()
    config.read(filename)

    # Server
    HOST = config.get("SERVER", "ip_address", fallback="0")
    # Use getint() for integer values
    PORT = config.getint("SERVER", "port", fallback=0)

    # Azimuth
    az_current_angle = float(config.get(
        "AZIMUTH CONTROL", "current_angle", fallback=0))
    az_start_angle = float(config.get(
        "AZIMUTH CONTROL", "start_point_degrees", fallback=0))
    az_end_angle = float(config.get(
        "AZIMUTH CONTROL", "end_point_degrees", fallback=0))
    az_step_size = float(config.get(
        "AZIMUTH CONTROL", "step_size", fallback=0))

    # Elevation
    el_current_angle = float(config.get(
        "ELEVATION CONTROL", "current_angle", fallback=0))
    el_start_angle = float(config.get(
        "ELEVATION CONTROL", "start_point_degrees", fallback=0))
    el_end_angle = float(config.get("ELEVATION CONTROL",
                         "end_point_degrees", fallback=0))
    el_step_size = float(config.get(
        "ELEVATION CONTROL", "step_size", fallback=0))

    # Measurement
    waveform = bool(config.get(
        "MEASUREMENT TYPE", "waveform", fallback=0))


def setup():
    global az_current_angle, az_start_angle, az_end_angle, az_step_size, el_current_angle, el_start_angle, el_end_angle, el_step_size, HOST, PORT, total_movement, current_key, total_movement_az, total_movement_el, waveform
    read_config()
    print("Controls:")
    print("  - Hold 'd' to move right.")
    print("  - Hold 'a' to move left.")
    print("  - Hold 'w' to move up.")
    print("  - Hold 's' to move down.")
    print("  - Press 'm' to increase azimuth step size.")
    print("  - Press 'n' to decrease azimuth step size.")
    print("  - Press 'k' to increase elevation step size.")
    print("  - Press 'j' to decrease elevation step size.")
    print("  - Press 'q' to exit setup.")

    while True:
        event = keyboard.read_event()  # Read the key event
        if event.event_type == keyboard.KEY_DOWN:  # Check if a key was pressed
            key = event.name

            if key == 'q':  # Quit the program
                print("Exiting...")
                break
            elif key == 'm':  # Increase step size
                if az_step_size < AZ_MAX_STEP:
                    # az_step_size = min(az_step_size + AZ_STEP_INCREMENT, AZ_MAX_STEP)
                    az_step_size = az_step_size + AZ_STEP_INCREMENT
                    print(
                        f"Azimuth step size increased to: {az_step_size:.2f}")
            elif key == 'n':  # Decrease step size
                if az_step_size > AZ_MIN_STEP:
                    # az_step_size = max(az_step_size - AZ_STEP_INCREMENT, AZ_MAX_STEP)
                    az_step_size = az_step_size - AZ_STEP_INCREMENT
                    print(
                        f"Aziimuth step size decreased to: {az_step_size:.2f}")
            elif key == 'k':  # Increase step size
                if el_step_size < EL_MAX_STEP:
                    el_step_size = el_step_size + EL_STEP_INCREMENT
                    print(
                        f"Elevation step size increased to: {el_step_size:.2f}")
            elif key == 'j':  # Decrease step size
                if el_step_size > EL_MIN_STEP:
                    el_step_size = el_step_size - EL_STEP_INCREMENT
                    print(
                        f"Elevation step size decreased to: {el_step_size:.2f}")
            elif key in ('d', 'a'):  # Start movement tracking
                if key != current_key:  # If a new key is pressed, reset total movement
                    total_movement_az = 0.0
                    current_key = key
            elif key in ('w', 's'):  # Start movement tracking
                if key != current_key:  # If a new key is pressed, reset total movement
                    total_movement_el = 0.0
                    current_key = key

        # Movement loop (runs while a key is being held)
        if current_key:
            if current_key == 'd':
                movement = float(az_step_size)
            elif current_key == 'a':
                movement = -1 * float(az_step_size)
            elif current_key == 'w':
                movement = float(el_step_size)
            elif current_key == 's':
                movement = -1 * float(el_step_size)
            else:
                movement = 0
            # movement = az_step_size if current_key == 'd' else -az_step_size
            if key in ('d', 'a'):
                send_command(f'move_az_DM542T.py:{movement}')
                total_movement_az += movement  # Accumulate movement in the correct direction
                print(f"Moved azimuth {total_movement_az:.2f} degrees")
            if key in ('w', 's'):
                send_command(f'move_el_DM542T.py:{movement}')
                total_movement_el += movement  # Accumulate movement in the correct direction
                print(f"Moved elevation {total_movement_el:.2f} degrees")

            time.sleep(SEND_DELAY)

        # If no key is being held, reset movement tracking
        if not event.event_type == keyboard.KEY_DOWN:
            total_movement = 0.0
            current_key = None
    # send_command(f'reset_encoder.py')
    az_current_angle = 0
    el_current_angle = 0

# Generates a matrix of zeroes for recording


def generate_measurement_array(el_sweep_size, el_step_size, az_sweep_size, az_step_size):
    az_values = int(az_sweep_size/az_step_size) + 1
    el_values = int(el_sweep_size/el_step_size) + 1

    zero_grid = np.zeros((el_values, az_values))
    peak_val = np.zeros((el_values, az_values))
    az_angle = np.zeros((el_values, az_values))
    el_angle = np.zeros((el_values, az_values))
    peak_freq = np.zeros((el_values, az_values))

    return zero_grid, peak_val, peak_freq, az_angle, el_angle

# Pause functionality for 2D sweep


def wait_for_resume():
    global paused
    # Wait until 'r' is pressed to resume the sweep
    print("Sweep paused. Press 'r' to resume...")
    while paused:
        if keyboard.is_pressed('r'):  # Resume when 'r' is pressed
            paused = False
            print("Resuming sweep...")
            break
        time.sleep(0.1)  # Sleep for a short time to avoid busy-waiting

# Moves stage to bottom left of measurement pattern to start control


def take_measurement(i, j, az_pos, el_pos, waveform):
    global peak_freq, peak_freq, az_angle
    time.sleep(settling_time)

    # Get the FFT Peak
    peakPWR_temp = scope.get_fft_peak(2)
    peak_freq_temp = scope.do_query(f":FUNCtion2:FFT:PEAK:FREQ?")
    peak_val[i][j] = peakPWR_temp
    peak_freq[i][j] = peak_freq_temp.strip('""')
    az_angle[i][j] = az_pos
    el_angle[i][j] = el_pos
    print("Saving to: ", i, ", ", j)

    if waveform:
        Infiniium.write(":DIGitize")
        time_values, voltage_values = get_waveform(1)
        filename = f"waveform_az{az_pos}_el{el_pos}.mat"
        scipy.io.savemat(save_folder+filename,
                         {'time': time_values, 'voltage': voltage_values})

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

    raw_data = Infiniium.query_binary_values(
        ":WAVeform:DATA?", datatype='b', container=np.array)

    time_values = np.linspace(
        x_origin, x_origin + x_increment * (num_points - 1), num_points)
    voltage_values = (raw_data * y_increment) + y_origin

    return time_values, voltage_values


def move_to_start():
    global az_current_angle, el_current_angle
    # We know that the controller should be at 0 in both elevation and azimuth to start
    # Move azimuth to start location
    print("Moving to:")
    print("Azimuth: ", az_start_angle)
    print("Elevation: ", el_start_angle)
    send_command(f'move_az_DM542T.py:{az_start_angle}')
    time.sleep(abs(az_start_angle * az_delay/.1))
    send_command(f'move_el_DM542T_absolute.py:{el_start_angle}')
    time.sleep(abs(el_start_angle * el_delay/.1))
    az_current_angle = az_start_angle
    el_current_angle = el_start_angle

    return 0


def return_to_start():
    global az_current_angle, el_current_angle
    # We know that the controller should be at 0 in both elevation and azimuth to start
    # Move azimuth to start location
    print("Moving to:")
    print("Azimuth: 0")
    print("Elevation: 0")
    send_command(f'move_az_DM542T.py:{-az_current_angle}')
    time.sleep(abs(az_start_angle * az_delay/.1))
    send_command(f'move_el_DM542T_absolute.py:{-el_current_angle}')
    time.sleep(abs(el_start_angle * el_delay/.1))
    az_current_angle = 0
    el_current_angle = 0

    return 0


def sweep_2D(grid):
    global az_current_angle, el_current_angle, paused, waveform
    num_cols = grid.shape[1]
    num_rows = grid.shape[0]

    for i in range(num_rows):
        print("Scanning row: ", i)
        if keyboard.is_pressed('p'):
            paused = True
            print("Sweep paused. Press 'r' to resume.")
        if paused:
            wait_for_resume()
        if i % 2 == 0:
            # Travel left to right on even indexed roads
            for j in range(num_cols):
                if keyboard.is_pressed('p'):
                    paused = True
                    print("Sweep paused. Press 'r' to resume.")
                if paused:
                    wait_for_resume()

                print("Current azimuth: ", round(az_current_angle, 2),
                      "    Current elevation: ", el_current_angle)
                time.sleep(abs(az_delay * az_step_size/.1))
                take_measurement(i, j, az_current_angle,
                                 el_current_angle, waveform)
                time.sleep(settling_time)
                send_command(f'move_az_DM542T.py:{az_step_size}')
                az_current_angle += az_step_size

        else:
            # Travel right to left on odd indexed roads
            for j in range(num_cols):
                if keyboard.is_pressed('p'):
                    paused = True
                    print("Sweep paused. Press 'r' to resume.")
                if paused:
                    wait_for_resume()
                send_command(f'move_az_DM542T.py:{-az_step_size}')
                az_current_angle -= az_step_size
                print("Current azimuth: ", round(az_current_angle, 2),
                      "    Current elevation: ", el_current_angle)
                time.sleep(abs(az_delay * az_step_size/.1))
                take_measurement(i, j, az_current_angle,
                                 el_current_angle, waveform)
                time.sleep(settling_time)
        if i != num_rows-1:
            send_command(
                f'move_el_DM542T_absolute.py:{el_start_angle + (i+1)*el_step_size}')
            el_current_angle += el_step_size
            time.sleep(abs(el_delay * el_step_size/.1))

        if keyboard.is_pressed('p'):
            paused = True
            print("Sweep paused. Press 'r' to resume.")

    print("Sweep complete!")
    return 0


# Code to be run
setup()
read_config()

grid, peak_val, peak_freq, az_angle, el_angle = generate_measurement_array(el_end_angle-el_start_angle,
                                                                           el_step_size, az_end_angle-az_start_angle, az_step_size)

send_command(f'move_el_DM542T.py:{0}')
move_to_start()


input("Press any key to continue with sweep")

sweep_2D(grid)

# Flip every other row of the matrix to fix serpentine traversal problems
az_angle[1::2] = az_angle[1::2, ::-1]
peak_freq[1::2] = peak_freq[1::2, ::-1]
peak_val[1::2] = peak_val[1::2, ::-1]

mdict = {
    'peak_val': peak_val,
    'peak_freq': peak_freq,
    'az_angle': az_angle,
    'el_angle': el_angle
}
scipy.io.savemat(save_path, mdict)

return_to_start()
