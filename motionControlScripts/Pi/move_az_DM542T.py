import RPi.GPIO as GPIO
import time
import sys

deg = float(sys.argv[1])
verbose = False
if len(sys.argv) == 3:
	if sys.argv[2] == "--verbose":
		verbose == True

# Set pin numbers under Broadcom Soc Channel numbering system
GPIO.setmode(GPIO.BCM)
PUL = 22
DIR = 27
ENA = 17

GPIO.setup(PUL, GPIO.OUT) # PUL-
GPIO.setup(DIR, GPIO.OUT) # DIR-
GPIO.setup(ENA, GPIO.OUT) # ENA-

# Initialize all to off
GPIO.output(ENA,True)
GPIO.output(PUL,False)
GPIO.output(DIR,False)

# Move desired number of steps
#steps = int(input('Enter number of steps: '))
#steps = -4
steps = round(400*abs(deg))

# Enable output and wait required time
GPIO.output(ENA,False)
time.sleep(0.3)

# Set direction 
if deg < 0:
	GPIO.output(DIR,True)
else:
	GPIO.output(DIR,False)


# Move desired number of steps
for i in range(abs(steps)):
	if verbose:
		print(i)
	GPIO.output(PUL,True)
	time.sleep(0.001)
	GPIO.output(PUL,False)
	time.sleep(0.001)

	
# Make sure outputs are in safe configuration after loop
GPIO.output(PUL,False)
GPIO.output(ENA,True)


#GPIO.cleanup()





