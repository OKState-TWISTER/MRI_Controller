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


def read_encoder_position():
    GPIO.output(CS_PIN, GPIO.LOW)
    time.sleep(0.000003)  # Wait 3 microseconds
    high_byte = spi.xfer2([AMT22_NOP])[0]
    time.sleep(0.000003)
    low_byte = spi.xfer2([AMT22_NOP])[0]
    time.sleep(0.000003)
    GPIO.output(CS_PIN, GPIO.HIGH)
    position = (high_byte << 8) | low_byte
    return position

# Function to verify checksum


def verify_checksum(message):
    checksum = 0x3  # Start with 0b11 as per datasheet
    for i in range(0, 14, 2):
        checksum ^= (message >> i) & 0x3
    return checksum == (message >> 14)

# Function to convert encoder position to degrees


def encoder_to_degrees(encoder_position):
    return (encoder_position / 16384.0) * 360.0

# Function to move stepper motor to desired angle


def move_motor_to_angle(deg):
    steps = round(400 * abs(deg))  # Convert degrees to steps
    GPIO.output(ENA, False)  # Enable motor
    time.sleep(0.3)  # Wait for motor to be enabled

    # Set direction
    if deg < 0:
        GPIO.output(DIR, True)
    else:
        GPIO.output(DIR, False)

    # Move motor the required number of steps
    for i in range(abs(steps)):
        GPIO.output(PUL, True)
        time.sleep(0.001)  # Adjust speed with delay
        GPIO.output(PUL, False)
        time.sleep(0.001)

# Main function to control stage elevation


def control_stage_elevation(target_deg):
    # Ensure motor is enabled
    GPIO.output(ENA, False)

    # Read the current position from the encoder and convert to degrees
    while True:
        # Read current encoder position
        encoder_position = read_encoder_position()

        if verify_checksum(encoder_position):
            current_deg = encoder_to_degrees(encoder_position)
            print(f"Current Position: {current_deg:.2f} degrees")
        else:
            print("Encoder position error.")
            continue

        # Check if the target angle is reached
        if abs(current_deg - target_deg) < MIN_ANGLE_RESOLUTION:  # You can adjust the tolerance here
            print("Target angle reached!")
            break  # Exit the loop once the target is reached

        # Move the stepper motor towards the target angle
        if current_deg < target_deg:
            move_motor_to_angle(target_deg - current_deg)
        else:
            move_motor_to_angle(current_deg - target_deg)

        time.sleep(0.5)  # Adjust as needed for smoother control

    # Disable motor after reaching the target position
    GPIO.output(ENA, True)


# Run the stage control
if __name__ == "__main__":
    try:
        control_stage_elevation(target_deg)
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()  # Cleanup GPIO pins on exit
