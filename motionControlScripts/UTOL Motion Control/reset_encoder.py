import RPi.GPIO as GPIO
import spidev
import time
import sys

# Define constants
PUL = 23
DIR = 24
ENA = 25
CS_PIN = 26  # GPIO pin used for Chip Select (CE0 for SPI on Raspberry Pi)
AMT22_NOP = 0x00
AMT22_ZERO = 0x70
MIN_ANGLE_RESOLUTION = .022

# SPI Setup for Encoder
spi = spidev.SpiDev()
spi.open(0, 0)  # Open SPI bus 0, device 0 (CE0)
spi.max_speed_hz = 500000  # Set SPI clock rate to 500 kHz (default for AMT22)
spi.mode = 0b00  # SPI Mode 0

# Setup GPIO for stepper motor control
GPIO.setmode(GPIO.BCM)
GPIO.setup(PUL, GPIO.OUT)
GPIO.setup(DIR, GPIO.OUT)
GPIO.setup(ENA, GPIO.OUT)
GPIO.setup(CS_PIN, GPIO.OUT)

GPIO.output(ENA, True)  # Disable motor initially
GPIO.output(PUL, False)  # Set pulse pin low initially
GPIO.output(DIR, False)  # Set direction initially

# Target elevation angle (in degrees) from command line argument
target_deg = float(sys.argv[1])

# Function to read encoder position


def set_zero_position():
    # Set CS to low
    GPIO.output(CS_PIN, GPIO.LOW)
    time.sleep(0.000003)  # Wait 3 microseconds

    # Send NO-OP command
    spi.xfer2([AMT22_NOP])
    time.sleep(0.000003)  # Wait 3 microseconds

    # Send ZERO command
    spi.xfer2([AMT22_ZERO])
    time.sleep(0.000003)  # Wait 3 microseconds

    # Set CS to high
    GPIO.output(CS_PIN, GPIO.HIGH)
    time.sleep(0.25)  # 250 ms delay for encoder reset


# Run the stage control
if __name__ == "__main__":
    try:
        set_zero_position()
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()  # Cleanup GPIO pins on exit
