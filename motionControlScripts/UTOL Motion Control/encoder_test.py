import RPi.GPIO as GPIO
import spidev
import time

# SPI setup
CS_PIN = 26  # GPIO pin used for Chip Select (CE0 for SPI on Raspberry Pi)
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


def main():
    set_zero_position()
    while True:
        # Read position from encoder
        encoder_position = read_encoder_position()

        # Verify checksum and convert to degrees
        if verify_checksum(encoder_position):
            encoder_position &= 0x3FFF  # Mask the checksum bits
            # Convert encoder position to degrees
            angle = (encoder_position / 16384.0) * 360.0
            print(
                f"Encoder Position: {encoder_position} (Raw), Angle: {angle:.4f} degrees")
        else:
            print("Encoder position error.")

        # Delay between reads (e.g., 100 ms)
        time.sleep(0.1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()  # Clean up GPIO on exit
