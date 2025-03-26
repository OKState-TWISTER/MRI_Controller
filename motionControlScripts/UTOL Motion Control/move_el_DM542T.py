import RPi.GPIO as GPIO
import spidev
import time
import sys

deg = float(sys.argv[1])

# GPIO Constants
PUL = 21
DIR = 20
ENA = 19

# SPI setup
CS_PIN = 25  # GPIO pin used for Chip Select (CE0 for SPI on Raspberry Pi)
# Serial baudrate (not needed for SPI, but useful for debug output)
BAUDRATE = 115200

# SPI commands
AMT22_NOP = 0x00
AMT22_ZERO = 0x70
AMT22_TURNS = 0xA0

# Initialize SPI
spi = spidev.SpiDev()
spi.open(0, 0)  # Open SPI bus 0, device 0 (CE0)
spi.max_speed_hz = 500000  # Set SPI clock rate to 500 kHz (default for AMT22)
spi.mode = 0b00  # SPI Mode 0

# Set up GPIO for chip select (CS) pin
GPIO.setmode(GPIO.BCM)
GPIO.setup(CS_PIN, GPIO.OUT)
GPIO.output(CS_PIN, GPIO.HIGH)  # Set CS to inactive (high)
GPIO.setmode(GPIO.BCM)

GPIO.setup(PUL, GPIO.OUT)
GPIO.setup(DIR, GPIO.OUT)
GPIO.setup(ENA, GPIO.OUT)
# GPIO.output(ENA, True)  # Disable motor initially
# GPIO.output(PUL, False)  # Set pulse pin low initially
# GPIO.output(DIR, False)  # Set direction initially


def read_encoder_position():
    # Set CS to low (active)

    GPIO.output(CS_PIN, GPIO.LOW)
    time.sleep(0.000003)  # Wait 3 microseconds

    # Send NO-OP command to read the position data
    high_byte = spi.xfer2([AMT22_NOP])[0]  # Get high byte
    time.sleep(0.000003)  # Wait 3 microseconds
    low_byte = spi.xfer2([AMT22_NOP])[0]  # Get low byte
    time.sleep(0.000003)  # Wait 3 microseconds

    # Set CS to high (inactive)
    GPIO.output(CS_PIN, GPIO.HIGH)

    # Combine the high and low byte to get the full 16-bit position
    position = (high_byte << 8) | low_byte
    return position


def verify_checksum(message):
    checksum = 0x3  # Start with 0b11 as per datasheet
    for i in range(0, 14, 2):
        checksum ^= (message >> i) & 0x3
    return checksum == (message >> 14)


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

# returns encoder angle in degrees


def encoder_to_degrees(encoder_position):
    return (encoder_position / 16384.0) * 360.0


def main(target):
    GPIO.output(ENA, False)  # Enable motor

    time.sleep(0.3)
    set_zero_position()
    encoder_target = target
    if (target >= 0):
        encoder_target = abs(target) % 360

    while True:
        # Read position from encoder
        encoder_position = read_encoder_position()
        encoder_position &= 0x3FFF
        current_angle = encoder_to_degrees(encoder_position)
        error = (encoder_target - current_angle + 540) % 360 - 180
        if (current_angle < 180):
            print(
                f"Angle: {-current_angle:.4f} degrees")
        else:
            print(
                f"Angle: {-(current_angle-360):.4f} degrees")
        if error > 0:
            GPIO.output(DIR, False)
        else:
            GPIO.output(DIR, True)
        if (abs(error) > .022):
            GPIO.output(PUL, True)
            time.sleep(0.001)  # Adjust speed with delay
            GPIO.output(PUL, False)
            time.sleep(0.001)
        else:
            break

        time.sleep(0.001)


if __name__ == "__main__":
    try:
        main(-deg)
       # GPIO.output(ENA, True)

    except KeyboardInterrupt:
        pass
    finally:
        print("Done!")  # GPIO.cleanup()  # Clean up GPIO on exit
