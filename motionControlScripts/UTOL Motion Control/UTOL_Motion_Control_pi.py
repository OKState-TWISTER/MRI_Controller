# UTOL Motion Control - Pi program

import socket
import subprocess
import RPi.GPIO as GPIO
import time

# Global Variables
HOST = '192.168.27.194'  # Raspberry Pi's IP address
PORT = 12345       # Arbitrary port

# # GPIO
# PUL_AZ = 22  # PUL pin for azimuth stepper motor
# DIR_AZ = 27  # DIR pin for azimuth stepper motor
# ENA_AZ = 17  # ENA pin for azimuth stepper motor
# PUL_EL = 23  # PUL pin for elevation stepper motor
# DIR_EL = 24  # DIR pin for azimuth stepper motor
# ENA_EL = 25  # ENA pin for azimuth stepper motor

# # Updates config file


# def gpio_setup():
#     GPIO.setmode(GPIO.BCM)  # Use the Broadcom Soc Channel numbering system
#     GPIO.setup(PUL_AZ, GPIO.OUT)  # PUL-
#     GPIO.setup(DIR_AZ, GPIO.OUT)  # DIR-
#     GPIO.setup(ENA_AZ, GPIO.OUT)  # ENA-
#     GPIO.setup(PUL_EL, GPIO.OUT)  # PUL-
#     GPIO.setup(DIR_EL, GPIO.OUT)  # DIR-
#     GPIO.setup(ENA_EL, GPIO.OUT)  # ENA-

#     # Initialize all to off/disabled
#     GPIO.output(ENA_AZ, True)  # The drive is disabled by a high state
#     GPIO.output(PUL_AZ, False)
#     GPIO.output(DIR_AZ, False)
#     GPIO.output(ENA_EL, True)  # The drive is disabled by a high state
#     GPIO.output(PUL_EL, False)
#     GPIO.output(DIR_EL, False)

# # Move a number of degrees in azimuth


# def move_az(deg):
#     # Motor is set to 800 steps/rev and 2 rev per degree of azimuth
#     # Therefore there are 400 motor steps per deg of azimuth rotation
#     steps_per_az_deg = 800
#     steps = steps_per_az_deg*deg

#     # Check that this was an integer number of steps
#     if steps != int(steps):
#         print("Error: Non-integer number of steps required")
#         return
#     else:
#         steps = int(steps)

#     # Enable output and wait required time (200ms minimum)
#     GPIO.output(ENA_AZ, False)
#     time.sleep(0.3)

#     # Set direction
#     if deg < 0:
#         GPIO.output(DIR_AZ, True)
#     else:
#         GPIO.output(DIR_AZ, False)
#     time.sleep(0.01)

#     # Move desired number of steps
#     for i in range(abs(steps)+1):
#         print(i)
#         GPIO.output(PUL_AZ, True)
#         time.sleep(0.002)
#         GPIO.output(PUL_AZ, False)
#         time.sleep(0.002)

#     time.sleep(0.1)
#     # Make sure outputs are in safe configuration after loop
#     GPIO.output(PUL_AZ, False)
#     # GPIO.output(ENA,True)


# def move_el(deg):

#     # Read current encoder angle
#     start_el_angle = get_el_angle()

#     # Enable output and wait required time (200ms minimum)
#     GPIO.output(ENA_EL, False)
#     time.sleep(0.3)

#     # Set direction
#     if deg < 0:
#         GPIO.output(DIR_EL, True)
#     else:
#         GPIO.output(DIR_EL, False)
#     time.sleep(0.01)

#     # Move motor until angle
#     while (get_el_angle() - start_el_angle < deg):  # Might need some sort of absolute value here
#         GPIO.output(PUL_EL, True)
#         time.sleep(0.002)
#         GPIO.output(PUL_EL, False)
#         time.sleep(0.002)
#     time.sleep(0.1)
#     # Make sure outputs are in safe configuration after loop
#     GPIO.output(PUL_EL, False)


# def get_el_angle():
#     return 0

# Executes a script from the socket if it is available


def execute_script(script_name, arguments):
    try:
        subprocess.run(["python", script_name] + arguments.split())
        print(f'Script "{script_name}" executed with arguments:', arguments)
    except FileNotFoundError:
        print(f'Script "{script_name}" not found.')


# Listen for commands from the PC on network
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()

    print("Server listening on", (HOST, PORT))

    while True:
        conn, addr = s.accept()
        print('Connected by', addr)

        with conn:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                # Expecting format: script_name:arguments
                script_data = data.decode().split(":")
                if len(script_data) != 2:
                    print("Invalid format. Expected: script_name:arguments")
                    continue
                script_name, arguments = script_data

                if script_name == 'move_az':
                    print(f"Moving Az {arguments} deg")
                    # move_az(float(arguments))
                if script_name == 'move_az':
                    print(f"Moving El {arguments} deg")
                    # move_el(float(arguments))
                else:
                    success = execute_script(script_name, arguments)
                    conn.send(("cmd_succ" if success else "cmd_fail").encode())