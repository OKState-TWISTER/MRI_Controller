# UTOL Motion Control - PC program

import socket
import socket
import keyboard  # Detects key input without pressing enter
import time
import configparser
import numpy as np
import sys
from twister_api.oscilloscope_interface import Oscilloscope
# from twister_api.waveformgen_interface import WaveformGenerator
# from twister_api.signalgen_interface import SignalGenerator
import twister_api.twister_utils as twister_utils
import twister_api.fileio as fileio
import scipy
import os
import datetime

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
SEND_DELAY = 0.1
settling_time = 1  # Time allowed for settling/averaging between measurements

# Server
HOST = ""
PORT = 0

# Save path
save_name = str(sys.argv[4])
# save_folder = 'C:/Users/Ethan Abele/OneDrive - Oklahoma A and M System/THz Jitter/measurements_29April2024/AzElSweep/'
save_folder = 'C:/Users/Ethan Abele/OneDrive - Oklahoma A and M System/Research/THz Jitter/python_scripts/tests_6Feb2025/'
# save_name = 'Az_sweep_El_000'

# Setup instrument
scope = Oscilloscope(
    visa_address="TCPIP0::192.168.27.10::inst0::INSTR", debug=True)
# scope = Oscilloscope(visa_address="TCPIP0::10.10.10.10::inst0::INSTR",debug=True)


# Function to send motion requests to the Raspberry Pi server


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

    # Write configuration to file
    with open(filename, "w") as configfile:
        config.write(configfile)

    print(f"Configuration file '{filename}' generated successfully.")

# Reads config file and updates corresponding global variables


def read_config(filename="config.ini"):
    global az_current_angle, az_start_angle, az_end_angle, az_step_size, el_current_angle, el_start_angle, el_end_angle, el_step_size, HOST, PORT
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


def setup():
    global az_current_angle, az_start_angle, az_end_angle, az_step_size, el_current_angle, el_start_angle, el_end_angle, el_step_size, HOST, PORT, total_movement, current_key, total_movement_az, total_movement_el
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
                print(f"Moved azimuth {total_movement_el:.2f} degrees")

            time.sleep(SEND_DELAY)

        # If no key is being held, reset movement tracking
        if not event.event_type == keyboard.KEY_DOWN:
            total_movement = 0.0
            current_key = None
    send_command(f'reset_encoder.py')


def generate_traversal(start_az, end_az, start_el, end_el, step_size_az, step_size_el):
    """
    Generate a 2D traversal matrix with elevation and azimuth points in a serpentine pattern.

    Parameters:
    - start_az: Starting azimuth (degrees)
    - end_az: Ending azimuth (degrees)
    - start_el: Starting elevation (degrees)
    - end_el: Ending elevation (degrees)
    - step_size_az: Step size for azimuth (degrees)
    - step_size_el: Step size for elevation (degrees)

    Returns:
    - traversal_matrix: A 2D matrix of [elevation, azimuth] pairs
    """
    # Generate ranges for azimuth and elevation
    azimuth_range = np.arange(start_az, end_az + step_size_az, step_size_az)
    elevation_range = np.arange(start_el, end_el + step_size_el, step_size_el)

    # Create a 2D grid of points
    traversal_points = []

    for i, elevation in enumerate(elevation_range):
        if i % 2 == 0:
            # Even rows: traverse left-to-right
            row = [(elevation, azimuth) for azimuth in azimuth_range]
        else:
            # Odd rows: traverse right-to-left
            row = [(elevation, azimuth) for azimuth in reversed(azimuth_range)]

        traversal_points.extend(row)

    # Convert the points to a 2D matrix (list of tuples: (elevation, azimuth))
    traversal_matrix = np.array(traversal_points)

    return traversal_matrix


def run_2D_sweep(scope, start_az, start_el, end_az, end_el, step_size_az, step_size_el, save_folder):
    """
    Perform a 2D sweep across the azimuth and elevation range and record measurements.

    Parameters:
    - scope: The instrument used for measurement (e.g., oscilloscope)
    - start_az: Starting azimuth (degrees)
    - start_el: Starting elevation (degrees)
    - end_az: Ending azimuth (degrees)
    - end_el: Ending elevation (degrees)
    - step_size_az: Step size for azimuth (degrees)
    - step_size_el: Step size for elevation (degrees)
    - save_folder: Folder to save the measurements

    Returns:
    - None
    """
    global az_current_angle, el_current_angle  # Declare global variables

    # Initialize current positions to the start values
    az_current_angle = start_az
    el_current_angle = start_el

    # Generate the traversal matrix (serpentine pattern)
    traversal_matrix = generate_traversal(
        start_az, end_az, start_el, end_el, step_size_az, step_size_el)

    # Initialize arrays to store peak values and frequencies
    peak_val = []
    peak_freq = []

    # Move to the bottom-left corner first (start from the last elevation and first azimuth)
    # Bottom left of the matrix (last elevation, first azimuth)
    first_point = traversal_matrix[-1, 0]
    first_az, first_el = first_point

    # Calculate relative movement for azimuth and elevation to get to the bottom-left corner
    azimuth_move = first_az - az_current_angle
    elevation_move = first_el - el_current_angle

    # Move to the bottom-left corner
    if azimuth_move != 0:
        send_command(f'move_az_DM542T.py:{azimuth_move}')
    if elevation_move != 0:
        send_command(f'move_el_DM542T.py:{elevation_move}')

    # Update global positions after moving to the bottom-left corner
    az_current_angle = first_az
    el_current_angle = first_el

    # Traverse the 2D matrix in serpentine pattern
    for elevation, azimuth in traversal_matrix:
        # Check if 'q' is pressed to pause the sweep
        if keyboard.is_pressed('q'):  # If 'q' is pressed, pause the sweep
            print("Sweep paused. Press 'q' again to resume.")
            while True:
                if keyboard.is_pressed('q'):  # Wait for 'q' to be pressed again
                    print("Resuming sweep...")
                    break
                # Small delay to avoid high CPU usage during pause
                time.sleep(0.1)

        # Calculate relative movement needed for azimuth and elevation
        azimuth_move = azimuth - az_current_angle
        elevation_move = elevation - el_current_angle

        # Send movement commands for azimuth and elevation
        send_command(f'move_az_DM542T.py:{azimuth_move}')
        send_command(f'move_el_DM542T.py:{elevation_move}')

        # Update global positions after the move
        az_current_angle = azimuth
        el_current_angle = elevation

        # Rest briefly before taking measurements
        time.sleep(0.5)  # Adjust rest time if necessary

        # Take measurements
        peakPWR_temp = scope.get_fft_peak(2)  # Get peak power
        peak_freq_temp = scope.do_query(
            f":FUNCtion2:FFT:PEAK:FREQ?")  # Get peak frequency

        # Store the measurements
        peak_val.append(peakPWR_temp)
        peak_freq.append(peak_freq_temp)

    # Save measurements to the specified folder
    save_to_matlab(peak_val, peak_freq, save_folder)


def save_to_matlab(peak_val, peak_freq, save_folder):
    """
    Save the peak power and peak frequency data to a .mat file for MATLAB.

    Parameters:
    - peak_val: List of peak power values
    - peak_freq: List of peak frequency values
    - save_folder: Folder where the .mat file will be saved

    Returns:
    - None
    """
    # Create the save folder if it doesn't exist
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    # Prepare data for saving
    data_dict = {
        'peak_val': np.array(peak_val),
        'peak_freq': np.array(peak_freq)
    }

    # Save the data to a .mat file
    mat_file_path = os.path.join(save_folder, "sweep_data.mat")
    scipy.io.savemat(mat_file_path, data_dict)
    print(f"Measurements saved to {mat_file_path}")


# Code to be run
setup()
read_config()
run_2D_sweep(scope, az_start_angle, el_start_angle, az_end_angle,
             el_end_angle, az_step_size, el_step_size, save_folder)
