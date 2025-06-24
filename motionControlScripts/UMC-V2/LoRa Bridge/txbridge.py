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
import checksum

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
prev_packet = None

lora_tx = []
lora_rx = []
lora_last_cmd = []
lora_ready = True

await_handshake = False
needs_repeat = False

log = logger(level=LOG_LEVEL.DEBUG)

def proc_handshake(msg):
    if len(msg) > 8:
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
    return msg

def send(data_str):
    global rfm9x
    log.debug(f"[SEND] Sending: {data_str}")
    enc = data_str.encode()
    chk = checksum.calc(enc)
    rfm9x.send(chk)
    log.debug(f"[SEND] Data w/ Checksum: {chk}")

def send_bytes(data_bytes):
    global rfm9x
    log.debug(f"[SEND] Sending: {data_bytes}")
    chk = checksum.calc(data_bytes)
    rfm9x.send(chk)
    log.debug(f"[SEND] Data w/ Checksum: {chk}")

def check_lora():
    global lora_rx, lora_tx, rfm9x, await_handshake, lora_ready, lora_last_cmd, needs_repeat
    last_sent = 0
    while True:
        packet = rfm9x.receive()
        if packet:
            if checksum.check_msg(packet):
                log.debug(f"Passed checksum!")
                packet = packet[:-1] #This removes the checksum
                try:
                    log.debug(f"[LORA-RX] Raw Message: {packet}")
                    log.debug(f"Awaiting handsake? {'YES' if await_handshake else 'NO'}")
                    if await_handshake:
                        succ = proc_handshake(packet)
                        if succ:
                            log.info(f"[LORA-TX] Received Okay!")
                            lora_ready = True
                            await_handshake = False
                        else:
                            log.info(f"[LORA-TX] Received Repeat!")
                            needs_repeat = True

                    log.debug(f"Was a handshake? {'NO' if proc_handshake(packet) == packet else 'YES'}")
                    if proc_handshake(packet) == packet:
                        if await_handshake:
                            log.warn(f"[LORA-RX] Received a message, but expected a handshake!")
                        message = packet.decode('utf-8')
                        log.debug(f"[LORA-RX] MESSAGE: {message}")
                        lora_rx += message
                        log.info(f"[LORA-RX] Sending Okay")
                        send('OOOOOOOO')
                except Exception:
                    log.warn(f"[LORA-RX] Error receiving message. Requesting Repeat")
            else:
                log.warn(f"[LORA-RX] Checksum failed!")
                log.debug(f"[LORA-RX] Failed packet: {packet}")
                log.warn(f"[LORA-RX] Received corrupt packet, requesting repeat")
                send('RRRRRRRR')


        if len(lora_tx) > 0 and lora_ready:
            log.info(f"[LORA-TX] Sending {len(lora_tx[0])} bytes!")
            # rfm9x.send("".join(lora_tx).encode('utf-8'))
            send_bytes(bytes(lora_tx[0]))
            lora_last_cmd = lora_tx.pop(0)
            lora_ready = False
            await_handshake = True
            last_sent = time.time()
        elif not lora_ready and needs_repeat:
            last_sent = time.time()
            send_bytes(bytes(lora_last_cmd))
        elif not lora_ready and time.time() - last_sent > 5:
            log.warn(f"[LORA-TX] No response. Re-transmitting")
            last_sent = time.time()
            send_bytes(bytes(lora_last_cmd))
        


# Start background thread
lora_thread = threading.Thread(target=check_lora, daemon=True)
lora_thread.start()


HOST = '192.168.27.194'
PORT = 12345
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
display.fill(0)
display.text('Running Bridge', 35, 0, 1)
display.show()
log.info("Running Bridge Program")
while True:
    try:
        # conn, addr = sock.accept()
        sock.connect((HOST, PORT))
    except TimeoutError:
        log.warn(f"Failed to connect, retrying in 5 seconds")
        time.sleep(5)
        continue
    except ConnectionRefusedError:
        log.warn(f"Failed to connect, retrying in 5 seconds")
        time.sleep(5)
        continue

    log.info("Connected to controller. Running bridge!")
    while True:
        readable, _, _ = select.select([sock], [], [], 0)
        if readable:
            data_bytes = sock.recv(1024)
            if data_bytes:
                log.debug(f"[ETHERNET] Message received over ETH: {data_bytes.decode('utf-8')}")
                lora_tx.append(data_bytes)
                log.debug(f"[ETHERNET] lora_tx now: {lora_tx}")
        else:
            try:
                data = sock.recv(1, socket.MSG_DONTWAIT | socket.MSG_PEEK)
                if data == 0: # Will recv a 0 if the socket has closed.
                    break
            except BlockingIOError:
                pass # Still connected, so do nothing
            except ConnectionResetError:
                log.warn(f"[ETHERNET] ConnectionResetError")
                break
            except Exception as e:
                log.warn(f"[ETHERNET]Unhandled error. Exception: {e}")
                break
        if len(lora_rx) > 0:
            log.debug(f"[ETHERNET] data from LoRa: {''.join(lora_rx)}")
            try:
                sock.send(''.join(lora_rx).encode("utf-8"))
                lora_rx = []
            except BrokenPipeError:
                log.warn(f"Broken Pipe. Reopening socket")
                sock.close()
                break

        time.sleep(0.1)
        
