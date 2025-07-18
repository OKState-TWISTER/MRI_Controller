import time
import busio
from digitalio import DigitalInOut, Direction, Pull
import board
import adafruit_ssd1306
import adafruit_rfm9x
import threading
import socket
import select
import json
from logger import logger, LOG_LEVEL

# Create the I2C interface.
i2c = busio.I2C(board.SCL, board.SDA)

# 128x32 OLED Display
reset_pin = DigitalInOut(board.D4)
display = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c, reset=reset_pin)
# Clear the display.
display.fill(0)
display.show()
width = display.width
height = display.height

# Configure LoRa Radio
CS = DigitalInOut(board.CE1)
RESET = DigitalInOut(board.D25)
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, 915.0)
rfm9x.tx_power = 23
rfm9x.node = 1 # Set node ID to 1 for non-broadcast messages
rfm9x.destination = 2 # Set default destination to 2, the tx end
rfm9x.ack_delay = 0.5
rfm9x.ack_wait = 1.5
rfm9x.coding_rate = 8
#rfm9x.spread_factor = 12
rfm9x.enable_crc = True

lora_tx = []
lora_rx = []
lora_last_cmd = []

do_ack = True

log = logger(level=LOG_LEVEL.DEBUG)

log.debug(f"INIT RFM9X: \n\tTx Power: {rfm9x.tx_power}\n\tSpreading Factor: {rfm9x.spreading_factor}\n\tCRC Enabled: {rfm9x.enable_crc}")

def proc_handshake(msg):
    if len(msg) > 8:
        log.debug("[HANDSHAKE] TOO LONG")
        return msg
    for i in range(len(msg)):
        try:
            log.debug(f"[HANDSHAKE] chr(msg[{i}]) = {chr(msg[i])}")
            if chr(msg[i]) == 'O':
                #This is okay. No action necessary.
                return True
            if chr(msg[i]) == 'R':
                # This is a request to repeat
                return False
        except Exception:
            pass
    log.debug(f"[HANDSHAKE] NOT A HANDSHAKE")
    return msg

def send(data_str):
    global rfm9x, do_ack
    log.debug(f"[SEND] Sending: {data_str}")
    enc = data_str.encode()
    if do_ack:
        succ = rfm9x.send_with_ack(enc)
        print(f"[SEND] ACK: {succ}")
    else:
        rfm9x.send(enc)


def send_bytes(data_bytes):
    global rfm9x, do_ack
    log.debug(f"[SEND] Sending: {data_bytes}")
    if do_ack:
        succ = rfm9x.send_with_ack(data_bytes)
        print(f"[SEND] ACK: {succ}")
    else:
        rfm9x.send(data_bytes)

def check_lora():
    global lora_rx, lora_tx, rfm9x, lora_last_cmd
    last_sent = 0
    while True:
        packet = rfm9x.receive(with_ack=True)
        if packet:
            try:
                log.debug(f"[LORA-RX] Raw Message: {packet}")
                message = packet.decode('utf-8')
                lora_rx += message
            except Exception as e:
                log.warn(f"[LORA-RX] Error receiving message. Requesting Repeat")
                log.error(f"[LORA-RX] Error {e}")

        if len(lora_tx) > 0:
            log.info(f"[LORA-TX] Sending {len(lora_tx[0])} bytes!")
            send_bytes(bytes(lora_tx[0]))
            lora_last_cmd = lora_tx.pop(0)    

# Start background thread
lora_thread = threading.Thread(target=check_lora, daemon=True)
lora_thread.start()


HOST = '192.168.27.155'
PORT = 12345
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
while True:
    try:
        sock.bind((HOST, PORT))
        break
    except OSError:
        log.warn(f"OSError. Waiting")
        time.sleep(5)

sock.listen()
display.fill(0)
display.text('Running Bridge', 35, 0, 1)
display.show()
log.info("Running Bridge Program")
while True:
    log.info("[ETHERNET] Waiting for connection...")
    conn, addr = sock.accept()
    log.info("[ETHERNET] Connected")
    while True:
        readable, _, _ = select.select([conn], [], [], 0)
        if readable:
            data_bytes = None
            try:
                data_bytes = conn.recv(1024)
            except ConnectionResetError:
                log.warn("[ETHERNET] Connection Reset. Restarting Socket.")
                break
            except Exception as e:
                log.error(f"[ETHERNET] UNHANDLED ERROR: {e}")
                log.warn(f"[ETHERNET] Restarting socket.")
                break
            if data_bytes:
                log.debug(f"[ETHERNET] Message received over ETH: {data_bytes.decode('utf-8')}")
                # TODO: Check queue to see if received message is in queue
                if len(lora_tx) == 0:
                    lora_tx.append(data_bytes)
            else:
                log.warn(f"[ETHERNET] Socket disconnected. Closing...")
                break
        else:
            try:
                data = conn.recv(1, socket.MSG_DONTWAIT | socket.MSG_PEEK)
                if data == 0:
                    break
            except BlockingIOError:
                pass # Still connected, so do nothing
            except ConnectionResetError:
                log.debug("[ETHERNET] ConnectionResetError")
                break
            except Exception:
                log.debug("[ETHERNET] Unhandled error.")
                break
        
        if len(lora_rx) > 0:
            log.debug(f"[ETHERNET] data from LoRa: {''.join(lora_rx)}")
            conn.send("".join(lora_rx).encode("utf-8"))
            lora_rx = []
    


    time.sleep(0.1)
