import socket
import subprocess
import RPi.GPIO as GPIO
import time

HOST = '192.168.27.194'  # Raspberry Pi's IP address
PORT = 12345       # Arbitrary port


def execute_script(script_name, arguments):
    try:
        subprocess.run(["python", script_name] + arguments.split())
        print(f'Script "{script_name}" executed with arguments:', arguments)
    except FileNotFoundError:
        print(f'Script "{script_name}" not found.')


def move_az(deg):
    # Motor is set to 800 steps/rev and 2 rev per degree of azimuth
    # Therefore there are 400 motor steps per deg of azimuth rotation
    steps_per_az_deg = 800
    steps = steps_per_az_deg*deg

    # Check that this was an integer number of steps
    if steps != int(steps):
        print("Error: Non-integer number of steps required")
        return
    else:
        steps = int(steps)

    # Enable output and wait required time (200ms minimum)
    GPIO.output(ENA, False)
    time.sleep(0.3)

    # Set direction
    if deg < 0:
        GPIO.output(DIR, True)
    else:
        GPIO.output(DIR, False)
    time.sleep(0.01)

    # Move desired number of steps
    for i in range(abs(steps)+1):
        print(i)
        GPIO.output(PUL, True)
        time.sleep(0.002)
        GPIO.output(PUL, False)
        time.sleep(0.002)

    time.sleep(0.1)
    # Make sure outputs are in safe configuration after loop
    GPIO.output(PUL, False)
    # GPIO.output(ENA,True)


# Start by setting up the GPIO and motor control pins
GPIO.setmode(GPIO.BCM)  # Use the Broadcom Soc Channel numbering system
PUL = 22
DIR = 27
ENA = 17
GPIO.setup(PUL, GPIO.OUT)  # PUL-
GPIO.setup(DIR, GPIO.OUT)  # DIR-
GPIO.setup(ENA, GPIO.OUT)  # ENA-

# Initialize all to off/disabled
GPIO.output(ENA, True)  # The drive is disabled by a high state
GPIO.output(PUL, False)
GPIO.output(DIR, False)

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
                    move_az(float(arguments))
                else:
                    execute_script(script_name, arguments)
