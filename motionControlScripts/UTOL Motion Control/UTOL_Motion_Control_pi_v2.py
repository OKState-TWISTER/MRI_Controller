# UTOL Motion Control - Pi program

import socket
import subprocess
import RPi.GPIO as GPIO
import time
from DM542T import DM542T
# Global Variables
HOST = '192.168.27.154'  # Raspberry Pi's IP address
PORT = 12345       # Arbitrary port



def execute_script(script_name, arguments):
    try:
        change = 1.0
        if (script_name == "move_el_DM542T.py"):
            change = el_motor.move(float(arguments),set_home=True)
        elif ( script_name == "move_el_DM542T_absolute.py"):
            change = el_motor.move(float(arguments))
        elif (script_name == "move_az_DM542T.py"):
            az_motor.move(float(arguments))
        # subprocess.run(["python", script_name] + arguments.split())
        print(f'Script "{script_name}" executed with arguments:', arguments)
        return True, change
    except FileNotFoundError:
        print(f'Script "{script_name}" not found.')
        return False, None

if __name__ == "__main__":
    # Azimuth Pins
    # PUL = 13
    # DIR = 12
    # ENA = 6
    az_motor = DM542T(13, 12, 6)
    # Elevation Pins
    # PUL = 21
    # DIR = 20
    # ENA = 19
    el_motor = DM542T(21, 20, 19, True)
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
                        success, change = execute_script(script_name, arguments)
                        if success:
                            if script_name[5:7] == "el":
                                conn.send(f"cmd_succ_el:{change:.4f}".encode())
                            else:
                                conn.send(f"cmd_succ".encode())
                            
                        else:
                            conn.send("cmd_fail".encode())
