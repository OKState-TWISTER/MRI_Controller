# UTOL Motion Control - Pi program

import socket
import subprocess
import RPi.GPIO as GPIO
import time
from DM542T import DM542T
import json
from logger import logger, LOG_LEVEL
# Global Variables
HOST = '192.168.27.194'  # Raspberry Pi's IP address
PORT = 12345       # Arbitrary port

log = logger(level=LOG_LEVEL.DEBUG)

def execute_cmd(data):
    meta = data
    meta['res'] = {}
    if data['cmd'] == "move":
        if data['args']['pl'] == "el":
            change, raw = el_motor.move(float(data['args']['deg']), relative= True if data['args']['rel'] == True else False)
            meta['res']['ch'] = change
            meta['res']['succ'] = True
            meta['res']['raw'] = raw 
        elif data['args']['pl'] == "az":
            change, raw = az_motor.move(float(data['args']['deg']))
            meta['res']['ch'] = change
            meta['res']['succ'] = True
    elif data['cmd'] == "goto":
        change_el, raw_el = el_motor.move(float(data['args']['el']['deg']), relative= True if data['args']['el']['rel'] == True else False)
        meta['res']['el'] = {}
        meta['res']['el']['ch'] = change_el
        meta['res']['el']['succ'] = True
        meta['res']['el']['raw'] = raw_el
        change_az, _ = az_motor.move(float(data['args']['az']['deg']))
        meta['res']['az'] = {}
        meta['res']['az']['ch'] = change_az
        meta['res']['az']['succ'] = True
    elif data['cmd'] == "set_home":
        az_motor.set_home()
        el_motor.set_home()
        meta['res']['succ'] = True
    elif data['cmd'] == 'meas':
        if data['args']['type'] == 'jitter':
            dur = float(data['args']['duration'])
            t, v = el_motor.measure_jitter(dur*1000000) # Duration argument from cmd in ms, measure_jitter duration in ns
            meta['res']['t'] = t
            meta['res']['r'] = v
    else:
        log.warn(f"Could not find command: {data['cmd']}")
        meta['res']['succ'] = False
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
                log.warn(f"Address Already in use... trying again in 5 seconds")
                time.sleep(5)
        s.listen()

        log.info(f"Server listening on ({HOST}, {PORT})")

        last_cmd_time = 0
        tx = None
        allbytes = b''
        while True:
            conn, addr = s.accept()
            log.info(f'Connected by {addr}')

            with conn:
                while True:
                    data = conn.recv(1024)
                    allbytes += data
                    check = allbytes.decode()
                    if not data:
                        break
                    if check.find("/UTOL") == -1:
                        continue
                    rec_cmd = check.split("/UTOL")[0]
                    log.debug(f"RECEIVED CMD: {rec_cmd}")
                    allbytes = b''
                    cmd = json.loads(rec_cmd)
                    log.debug(f"cmd timestamp <= last_cmd_time -> {cmd['timestamp']} <= {last_cmd_time}")
                    if cmd['timestamp'] <= last_cmd_time:
                        log.warn(f"Detected repeat command!")
                        cnt = conn.send(f"{tx}/UTOL".encode())
                    else:

                    # metadata = execute_cmd(script_name, arguments)
                        metadata = execute_cmd(json.loads(rec_cmd))
                        last_cmd_time = cmd['timestamp']
                        tx = json.dumps(metadata)
                        while True:
                            try:
                                dummy = json.loads(tx)
                                break
                            except:
                                log.warn(f"Failed to properly encode the JSON object, trying again")
                                time.sleep(0.1)
                                tx = json.dumps(metadata)
                        log.debug(f"Sending: {len(tx)} bytes")
                        cnt = conn.send(f"{tx}/UTOL".encode())
