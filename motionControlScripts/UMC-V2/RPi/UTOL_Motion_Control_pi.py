# UTOL Motion Control - Pi program

import socket
import subprocess
import RPi.GPIO as GPIO
import time
from DM542T import DM542T
import json
# Global Variables
HOST = '192.168.27.194'  # Raspberry Pi's IP address
PORT = 12345       # Arbitrary port

def _execute_cmd(cmd, args, timestamp):
    try:
        meta = {}
        meta['cmd'] = cmd
        meta['arg'] = args
        meta['results'] = {}
        if cmd.find("move") >= 0:
            if cmd.find("el") >= 0:
                change, raw = el_motor.move(float(args), relative=True if script_name.find("absolute") == -1 else False)
                meta['results']['change'] = change
                meta['results']['success'] = True
                meta['results']['raw'] = raw 
            elif cmd.find("az") >= 0:
                change, raw = az_motor.move(float(args))
                meta['results']['change'] = change
                meta['results']['success'] = True
        elif cmd.find("set_home") >= 0:
            az_motor.set_home()
            el_motor.set_home()
            meta['results']['success'] = True
        elif cmd.find('meas') >= 0:
            if cmd.find('jitter') >= 0:
                t, v = el_motor.measure_jitter()
                meta['results']['time'] = t
                meta['results']['readings'] = v
        else:
            print(f"Could not find command: {cmd}")
            meta['results']['success'] = False
        return meta
        
    except FileNotFoundError:
        print(f'Script "{script_name}" not found.')
        return False, None
    except IndexError:
        print(f"Indexing issue. Malformed command? {cmd}")

def execute_cmd(data):
    meta = data
    meta['results'] = {}
    if data['cmd'] == "move":
        if data['args']['plane'] == "el":
            change, raw = el_motor.move(float(data['args']['degree']), relative= True if data['args']['relative'] == True else False)
            meta['results']['change'] = change
            meta['results']['success'] = True
            meta['results']['raw'] = raw 
        elif data['args']['plane'] == "az":
            change, raw = az_motor.move(float(data['args']['degree']))
            meta['results']['change'] = change
            meta['results']['success'] = True
    elif data['cmd'] == "set_home":
        az_motor.set_home()
        el_motor.set_home()
        meta['results']['success'] = True
    elif data['cmd'] == 'meas':
        if data['args']['type'] == 'jitter':
            t, v = el_motor.measure_jitter()
            meta['results']['time'] = t
            meta['results']['readings'] = v
    else:
        print(f"Could not find command: {data['cmd']}")
        meta['results']['success'] = False
    return meta

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
        while True:
            try:        
                s.bind((HOST, PORT))
                break
            except OSError:
                print(f"Address Already in use... trying again in 5 seconds")
                time.sleep(5)
        s.listen()

        print("Server listening on", (HOST, PORT))

        last_cmd_time = 0
        tx = None
        allbytes = b''
        while True:
            conn, addr = s.accept()
            print('Connected by', addr)

            with conn:
                while True:
                    #print(f"Listening for Data")
                    data = conn.recv(1024)
                    allbytes += data
                    check = allbytes.decode()
                    if not data:
                        break
                    if check.find("/UTOL") == -1:
                        continue
                    # Expecting format: script_name:arguments
                    # script_data = data.decode().split(":")
                    # if len(script_data) != 2:
                    #     print("Invalid format. Expected: script_name:arguments")
                    #     print(f"\t{data.decode()}")
                    #     continue
                    # script_name, arguments = script_data
                    rec_cmd = check.split("/UTOL")[0]
                    print(f"RECEIVED CMD: {rec_cmd}")
                    allbytes = b''
                    cmd = json.loads(rec_cmd)
                    print(f"cmd timestamp <= last_cmd_time -> {cmd['timestamp']} <= {last_cmd_time}")
                    if cmd['timestamp'] <= last_cmd_time:
                        print(f"Detected repeat command!")
                        cnt = conn.send(f"{tx}/UTOL".encode())
                    else:

                    # metadata = execute_cmd(script_name, arguments)
                        metadata = execute_cmd(json.loads(rec_cmd))
                        last_cmd_time = cmd['timestamp']
                        tx = json.dumps(metadata)
                        print(f"Sending: {len(tx)} bytes")
                        cnt = conn.send(f"{tx}/UTOL".encode())
                        #print(f"Actually sent: {cnt}")
