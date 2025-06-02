# UTOL Motion Control - Pi program

import socket
import subprocess
import RPi.GPIO as GPIO
import time
from DM542T import DM542T
import json
# Global Variables
HOST = '192.168.27.154'  # Raspberry Pi's IP address
PORT = 12345       # Arbitrary port



# def execute_script(script_name, arguments):
#     print(f"Executing {script_name}")
#     try:
#         change = 1 # Note: This isn't really called change anymore. Just don't have an easy way to swap this everywhere.
#         cmd = None
#         if (script_name == "move_el_DM542T.py"):
#             cmd = "el"
#             change = el_motor.move(float(arguments),relative=True)
#             return True, cmd, float(change)
#         elif ( script_name == "move_el_DM542T_absolute.py"):
#             cmd = "el"
#             change = el_motor.move(float(arguments),relative=False)
#             return True, cmd, float(change)
#         elif (script_name == "move_az_DM542T.py"):
#             cmd = "az"
#             change = az_motor.move(float(arguments))
#             return True, cmd, float(change)
#         elif (script_name == "measure_jitter"):
#             t, v = el_motor.measure_jitter(float(arguments))
#         # subprocess.run(["python", script_name] + arguments.split())
#         print(f'Script "{script_name}" executed with arguments:', arguments)
#         #print(f'With change {change}')
#         return False, None, None
#     except FileNotFoundError:
#         print(f'Script "{script_name}" not found.')
#         return False, None

def execute_cmd(cmd, args):
    try:
        meta = {}
        meta['cmd'] = cmd
        meta['arg'] = args
        meta['results'] = {}
        if cmd.find("move") >= 0:
            if cmd.find("el") >= 0:
                change = el_motor.move(float(args), relative=True if script_name.find("absolute") == -1 else False)
                meta['results']['change'] = change
                meta['results']['success'] = True
            elif cmd.find("az") >= 0:
                change = az_motor.move(float(args))
                meta['results']['change'] = change
                meta['results']['success'] = True
        elif cmd.find("set_home") >= 0:
            az_motor.set_home()
            el_motor.set_home()
            meta['results']['success'] = True
        else:
            print(f"Could not find command: {cmd}")
            meta['results']['success'] = False
        return meta
        
    except FileNotFoundError:
        print(f'Script "{script_name}" not found.')
        return False, None
    except IndexError:
        print(f"Indexing issue. Malformed command? {cmd}")

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
    el_motor = DM542T(21, 20, 19, True, True)
    # Listen for commands from the PC on network
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()

        print("Server listening on", (HOST, PORT))

        while True:
            conn, addr = s.accept()
            #print('Connected by', addr)

            with conn:
                while True:
                    #print(f"Listening for Data")
                    data = conn.recv(1024)
                    if not data:
                        break
                    # Expecting format: script_name:arguments
                    script_data = data.decode().split(":")
                    if len(script_data) != 2:
                        print("Invalid format. Expected: script_name:arguments")
                        print(f"\t{data.decode()}")
                        continue
                    script_name, arguments = script_data

                    print(f"Script {script_name}")

                    metadata = execute_cmd(script_name, arguments)
                    tx = json.dumps(metadata)
                    conn.send(tx.encode())
