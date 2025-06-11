import keydata
import boto3
import json

# Import Python System Libraries
import os
import time 
from time import sleep
from datetime import datetime
import serial
import threading
# Import Blinka Libraries
import busio
from digitalio import DigitalInOut, Direction, Pull
import board
# Import the SSD1306 module.
import adafruit_ssd1306
# Import RFM9x
import adafruit_rfm9x

#boto3 iot-core data client
iot_data_client = boto3.client('iot-data', region_name=keydata.region_name, aws_access_key_id=keydata.access_key_ID, aws_secret_access_key=keydata.secret_access_key)
dynamodb_client = boto3.client('dynamodb')
dynamodb_resource = boto3.resource('dynamodb')
table = dynamodb_resource.Table("SoilTable")

# Button A
btnA = DigitalInOut(board.D5)
btnA.direction = Direction.INPUT
btnA.pull = Pull.UP

# Button B
btnB = DigitalInOut(board.D6)
btnB.direction = Direction.INPUT
btnB.pull = Pull.UP

# Button C
btnC = DigitalInOut(board.D12)
btnC.direction = Direction.INPUT
btnC.pull = Pull.UP

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
rfm9x.tx_power = 5
prev_packet = None

start = time.time()

# Time to run
PACKET_TIMEOUT = 0.5 #seconds

temptime = datetime.utcnow()
filename = "/home/pi/logs/{:0>2d}-{:0>2d}-{:0>2d}_{:0>2d}-{:0>2d}_data_log.csv".format(temptime.month,temptime.day, temptime.year, temptime.hour, temptime.minute)
file = open(filename, "w")
i=0
if os.stat(filename).st_size == 0:
        file.write("Time,RSSI (dBm),Latitude,Longitude\n")

no_packet_start_time = time.time()
shadow_check_time = time.time()
shadow_water = "false"

while True:
    if time.time() > shadow_check_time + 5:
        shadow_check_time = time.time()
        print("Checking thing shadow")
        thingShadow = iot_data_client.get_thing_shadow(thingName=keydata.thingName, shadowName=keydata.shadowName)['payload'].read()
        shadowData = json.loads(thingShadow.decode("utf-8"))
        if not shadow_water == shadowData['state']['desired']['water']:
            packDatW = {}
            packDatW['command'] = "water"
            packDatW['active'] = shadowData['state']['desired']['water']
            rfm9x.send(bytearray(json.dumps(packDatW).encode()))
            rfm9x.receive(timeout=5)
            if not packet is None:
                shadow_water = shadowData['state']['desired']['water']



    packet = None
    # draw a box to clear the image
    display.fill(0)
    display.text('RasPi LoRa', 35, 0, 1)

    #send command to measure soil
    packDatM = {}
    packDatM['command'] = "measure"
    rfm9x.send(bytearray(json.dumps(packDatM).encode()))


    # check for packet rx
    packet = rfm9x.receive(timeout=PACKET_TIMEOUT)
    if packet is None: #If the timeout is reached
        display.show()
        display.text('- PKT LOSS -', 35, 20, 1)
        print("Packet Loss")
        file.write("{},{}\n".format(datetime.now(), "Packet Loss"))
        no_packet_start_time = time.time()

    else:
        # Display the packet text and rssi
        display.fill(0)
        prev_packett = packet
        #Filtering out packets with non-digits. Bad data
        if prev_packett.isdigit():
                prev=float(prev_packett)
                #Convert packet's data to a scale of 0 to 100
                prev_packet=-0.008547008547008548*prev+239.31623931623935
                #packet_text = str(prev_packet, "utf-8")
                display.text('Moisture: ', 0, 0, 1)
                #display.text(packet_text, 25, 0, 1)
                display.text(format(prev_packet), 0, 10, 1)
                #print(prev_packett)
                print("\nRaw Data "+str(float(prev_packett)))
                print("Soil Moisture "+ str(prev_packet))
                received_power=rfm9x.last_rssi
                print("Receiver_Signal_Strength:{0} dB".format(received_power))
                #snr=rfm9x.last_snr
                #print("SNR:  "+str(snr))
                #received_pow = str(received_power, "utf-8")
                display.text('RX_Power: ', 1, 20, 2)
                display.text(format(received_power), 55, 20, 2)
                #time.sleep(0.1)
         

                #i=i+1
                now = datetime.utcnow()
                #file.write(str(now)+","+str(i)+","+str(-i)+","+str(i-10)+","+str(i+5)+","+str(i*i)+"\n")
                file.write("{},{}\n".format(str(now), received_power))
                file.flush()
                datDB = {'SoilPartition': 'SOIL', 'Moisture': str(prev_packet)}
                table.put_item(Item=datDB)
    
    
    

    if  packet==None and time.time()>no_packet_start_time+0.5:
        file.write("{},{}\n".format(str(datetime.now()), "Packet Loss"))
        file.flush()
        no_packet_start_time=time.time()
    display.show()
    #time.sleep(0.1)

    #If buttonA is pressed, then exit the while loop.
    #   This will replace the previous if statement to exit based on time.
    ##  This allows us to stop when we are done flying the drone, not when the time is up
    if (btnA.value == False):
        print("BtnA pressed")
        break
    if (btnB.value == False):
        print("BtnB pressed")
    if (btnC.value == False):
        print("BtnC pressed")


file.close()
display.fill(0)
display.text("Exited...", 15, 20, 1)
display.show()
#print("Finished")
