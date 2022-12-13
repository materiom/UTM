# Use the pyserial library
import serial
import time
import sys
import json
from collections import deque
import numpy as np

import time
import sys
from threading import Thread


class Extensometer:
    def __init__(self, config=None):
        self.config = config
        self.serial = None
        self.connected = False
        self.displacement = 0.0
        self.time = 0.0
        self.speed = 0.0
        self.q_length = 10
        
        self.Q = deque(maxlen=self.q_length)
        
        self.init(config)
        
        
    def init(self, config=None):
        if config == None:
                f = open("./config/user.db","r")
                #f = open("../../config/user.db","r")
                self.config = json.load(f)["modules"]["digital_extensometer"]
                #print(self.config)
        else:
            self.config = config
        
        self.limits = self.config["limits"]

        self.serial = serial.Serial(port=self.config["port"], baudrate=self.config["baudrate"], timeout=.1) # Connect to the serial port that has the digital callipers on
        
        return self
        

    
    def start(self):
        """ Threading to read values """
        self.connected = True
        t = Thread(target=self.update, args=[])
        t.daemon = True
        t.start()
        print("Extensometer Started",flush=True)
        
        return self

    
    def stop(self):
        """ Stop reading """
        
        self.connected = False
        self.serial.close()
        
        
        return self
        
        

    def update(self):
        
        while True:
            if self.serial.inWaiting() > 0: # If the serialport is ready to read...do this
                # Read a line of data from the serial port, and strip the endline characters
                line = self.serial.readline().strip() ## Read a line of data up to a newline character
                line = line.decode("utf8") #  decode bytes into a string
                if line != "": # If the line is not an empty string...do this
                    # Decode the line string as utf8 and split it using commas as the delimiter
                    line = line.split(" ")
                    # We are expecting 3 items of data
                    if len(line) == 2: # line[0] = time, line[1] = displacement, line[2] = speed
                        # print the values to the UTM process so it can be logged and displayed in the GUI
                        disp = float(line[0]) # Microns
                        speed = float(line[1]) # mm per second
                        disp = disp/1000.0 # convert microns to millimeters
                        
                        self.displacement = disp
                        
                        self.Q.append([time.time(),disp]) # Values are coming in as microns
                        
                        if len(self.Q) > 1:
                                delta_d = abs(self.Q[-1][1] - self.Q[0][1])
                                delta_t = self.Q[-1][0] - self.Q[0][0]
                                speed = delta_d / delta_t
                                #speed = np.mean(speed)
                                self.speed = speed
                        
                        
                        #"""
                        
                        
                    #time.sleep(0.01) ## Comment out to read as fast as the digital scale will allow
                            
    def read(self):
        # Return these two values
        return self.displacement, self.speed

    def exit(self):
        GPIO.cleanup()
        sys.exit()
        
        


if __name__ == "__main__":
    # If we are running this script as a standalone program for debugging...
    # Start the extensometer
    e = Extensometer().init()
    e.start()
    
    while True:
        # Read continuously at about 10Hz (using time.sleep(0.1))
        print(e.read())
        # delay for a short while between reads
        time.sleep(0.1)

