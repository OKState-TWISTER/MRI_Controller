import RPi.GPIO as GPIO
import time
import sys
import spidev

# This class is nearly a 1:1 copy of previous code. 
# As such, this will not be well commented, because I'm not 100% sure why everything is happening.
# But the old stuff works...
class DM542T:
    def __init__(self, PUL_pin, DIR_pin, ENA_pin, encoder=None, flip_dir=False):
        print(f"Initializing DM542T...")
        GPIO.setwarnings(False)
        self.PUL = PUL_pin
        self.DIR = DIR_pin
        self.ENA = ENA_pin
        self.flip_dir = flip_dir
        self.encoder = encoder
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.PUL, GPIO.OUT)
        GPIO.setup(self.DIR, GPIO.OUT)
        GPIO.setup(self.ENA, GPIO.OUT)

        time.sleep(0.1)

        self.current_angle = 0

        if self.encoder is not None:
            # SPI setup
            self.CS_PIN = 25  # GPIO pin used for Chip Select (CE0 for SPI on Raspberry Pi)
            # Serial baudrate (not needed for SPI, but useful for debug output)
            self.BAUDRATE = 115200

            GPIO.setup(self.CS_PIN, GPIO.OUT)
            GPIO.output(self.CS_PIN, GPIO.HIGH)
            
            # SPI commands
            self.AMT22_NOP = 0x00
            self.AMT22_ZERO = 0x70
            self.AMT22_TURNS = 0xA0
            # Initialize SPI
            self.spi = spidev.SpiDev()
            self.spi.open(0, 0)  # Open SPI bus 0, device 0 (CE0)
            self.spi.max_speed_hz = 500000  # Set SPI clock rate to 500 kHz (default for AMT22)
            self.spi.mode = 0b00  # SPI Mode 0
            self.set_zero_position()
    def set_home(self):
        self.current_angle = 0
        if self.encoder is not None:
            self.set_zero_position()
        return True

    
    def move(self, deg, verbose=False, relative=False):
        GPIO.output(self.ENA, False)
        time.sleep(.3)
        if self.encoder is None:
            steps = round(400*abs(deg))
            # Enable output and wait required time

            # Set direction
            if deg < 0:
                GPIO.output(self.DIR, False if self.flip_dir else True)
            else:
                GPIO.output(self.DIR, True if self.flip_dir else False)
            # Move desired number of steps
            for i in range(abs(steps)):
                #print(i)
                GPIO.output(self.PUL, True)
                time.sleep(0.001)
                GPIO.output(self.PUL, False)
                time.sleep(0.001)


            # Make sure outputs are in safe configuration after loop
            GPIO.output(self.PUL, False)
            self.current_angle = self.current_angle + deg
            return self.current_angle
        else:
            # print(f"Encoder...")
            encoder_target = deg
            if relative:
                #print(f"CURRENT ANGLE: {self.current_angle}")
                encoder_target += self.current_angle
            #print(f"TARGET: {encoder_target}")
            if (deg >= 0):
                encoder_target = abs(encoder_target) % 360

            while True:
                # Read position from encoder
                encoder_position = self.read_encoder_position()
                encoder_position &= 0x3FFF
                current_angle = self.degrees_to_antenna_angle(self.encoder_to_degrees(encoder_position))
                error = encoder_target - current_angle
                #if (current_angle < 180):
                #    print(
                #        f"Angle: {-current_angle:.4f} degrees")
                #else:
                #    print(
                #        f"Angle: {-(current_angle-360):.4f} degrees")
                #print(f"Angle: {current_angle:.4f}")
                if error > 0:
                    GPIO.output(self.DIR, True if self.flip_dir else False)
                else:
                    GPIO.output(self.DIR, False if self.flip_dir else True)
                if (abs(error) > .021):
                    #print(f"ERROR: {error}")
                    #print(f"TARGET: {encoder_target}")
                    #print(f"CURRNET: {current_angle}")
                    GPIO.output(self.PUL, True)
                    time.sleep(0.001)  # Adjust speed with delay
                    GPIO.output(self.PUL, False)
                    time.sleep(0.001)
                #elif (abs(error) > .01):
                #    GPIO.output(self.PUL, True)
                #    time.sleep(0.05)  # Adjust speed with delay
                #    GPIO.output(self.PUL, False)
                #    time.sleep(0.05)
                #elif (abs(error) > .005):
                #    GPIO.output(self.PUL, True)
                #    time.sleep(0.01)  # Adjust speed with delay
                #    GPIO.output(self.PUL, False)
                #    time.sleep(0.01)
                else:
                    self.current_angle = current_angle
                    #print(f"NEW ANGLE: {self.current_angle}")
                    return current_angle

                time.sleep(0.001)
                
    def move_to(self, deg, verbose=False):
        print(f"TODO")

    def read_encoder_position(self):
    # Set CS to low (active)

        GPIO.output(self.CS_PIN, GPIO.LOW)
        time.sleep(0.000003)  # Wait 3 microseconds

        # Send NO-OP command to read the position data
        high_byte = self.spi.xfer2([self.AMT22_NOP])[0]  # Get high byte
        time.sleep(0.000003)  # Wait 3 microseconds
        low_byte = self.spi.xfer2([self.AMT22_NOP])[0]  # Get low byte
        time.sleep(0.000003)  # Wait 3 microseconds

        # Set CS to high (inactive)
        GPIO.output(self.CS_PIN, GPIO.HIGH)

        # Combine the high and low byte to get the full 16-bit position
        position = (high_byte << 8) | low_byte
        return position


    def verify_checksum(self,message):
        checksum = 0x3  # Start with 0b11 as per datasheet
        for i in range(0, 14, 2):
            checksum ^= (message >> i) & 0x3
        return checksum == (message >> 14)


    def set_zero_position(self):
        # Set CS to low
        GPIO.output(self.CS_PIN, GPIO.LOW)
        time.sleep(0.000003)  # Wait 3 microseconds

        # Send NO-OP command
        self.spi.xfer2([self.AMT22_NOP])
        time.sleep(0.000003)  # Wait 3 microseconds

        # Send ZERO command
        self.spi.xfer2([self.AMT22_ZERO])
        time.sleep(0.000003)  # Wait 3 microseconds

        # Set CS to high
        GPIO.output(self.CS_PIN, GPIO.HIGH)
        time.sleep(0.25)  # 250 ms delay for encoder reset

    # returns encoder angle in degrees


    def encoder_to_degrees(self, encoder_position):
        return (encoder_position / 16384.0) * 360.0

    def degrees_to_antenna_angle(self, encoder_degrees):
        if encoder_degrees < 180:
            return -1 * encoder_degrees
        else:
            return 360 - encoder_degrees

    def measure_jitter(self, duration_ns=10000000):
        start = time.time_ns()
        values = []
        times = []
        while True:
            values.append(self.read_encoder_position())
            times.append(time.time_ns())
            if times[-1] - start >= duration_ns:
                break
        return times, values

if __name__ == "__main__":
    print(f"Debugging motor controls")
    el = DM542T(21, 20, 19, True)
    while True:
        print(f"Encoder Angle: {el.degrees_to_antenna_angle(el.encoder_to_degrees(el.read_encoder_position() & 0x3FFF))}")
