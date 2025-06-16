import time
import busio
from digitalio import DigitalInOut, Direction, Pull
import board
import adafruit_ssd1306
import adafruit_rfm9x
import threading
import socket
import select

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

def check_lora():
    global lora_rx, lora_tx, rfm9x
    while True:
        packet = rfm9x.receive()
        if packet:
            try:
                message = packet.decode('utf-8')
                print(f"MESSAGE: {message}")
                lora_rx += message
                rfm9x.send('okay\LORA'.encode('utf-8'))
            except Exception:
                print(f"[LORA] Error receiving message. Requesting Repeat")
                rfm9x.send('repeat\LORA'.encode('utf-8'))

        if len(lora_tx) > 0:
            print(f"[LORA] Sending {len(lora_tx)} bytes!")
            # rfm9x.send("".join(lora_tx).encode('utf-8'))
            rfm9x.send(bytes(lora_tx))
            while True:
                res = rfm9x.receive()
                if res:
                    try:
                        msg = res.decode('utf-8')
                        if msg == "okay\LORA":
                            break
                    except Exception:
                        rfm9x.send('repeat\LORA'.encode('utf-8'))
            lora_tx = []


# Start background thread
lora_thread = threading.Thread(target=check_lora, daemon=True)
lora_thread.start()


HOST = '192.168.27.155'
PORT = 12345
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((HOST, PORT))
# sock.setblocking(False)
# sock.settimeout(1.0)
sock.listen()
display.fill(0)
display.text('Running Bridge', 35, 0, 1)
display.show()
try:
    conn, addr = sock.accept()
    while True:
        readable, _, _ = select.select([conn], [], [], 0)
        if readable:
            data_bytes = conn.recv(1024)
            if data_bytes:
                print(f"DATA: {data_bytes.decode('utf-8')}")
                lora_tx += data_bytes
        if len(lora_rx) > 0:
            print(f"LoRa -> Ethernet: {lora_rx}")
            conn.send("".join(lora_rx).encode("utf-8"))
            lora_rx = []
        


        time.sleep(0.1)
except KeyboardInterrupt:
    print("Exiting...")
    conn.close()
    sock.close()
