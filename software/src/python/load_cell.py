import time
import sys
import json
from threading import Thread
import numpy as np
from collections import deque
from statistics import mean, stdev

import RPi.GPIO as GPIO
GPIO.setwarnings(False)

from hx711 import HX711 # Amplifier 1 - 2 wire (not i2c)
import PyNAU7802 # Amplifier 2 - i2c
import smbus2



class LoadCell:
    def __init__(self, config=None):
        self.config = config
        self.unit = None
        self.connected = False
        self.readings = deque(maxlen=7)
        self.mean_value = 0.0
        self.stdev_value = 0.0
        # Define the measurements in different units
        self.value_bits = 0
        self.value_g = 0.0
        self.value_N = 0.0
        self.value_kN = 0.0
        
        self.bus = None
        self.init(config)
            
            
        
    def init(self, config=None):
        if config == None:
            f = open("./config/user.db","r") # Use this normally
            #f = open("../../config/user.db","r") # Use this is you are running this script as standalone     
            config = json.load(f)
            self.config = config["modules"]["load_cell"]
        
        self.limits = self.config["limits"]


        if self.config["amplifier"] == "HX711" :
            #print(self.config["gpio"]["data"], self.config["gpio"]["clock"])
            self.init_hx711()
            return self

        elif self.config["amplifier"] == "NAU7802":
            self.init_nau7802()
            return self
        
        return self
        
            
    def init_hx711(self):
        print("Initialising HX711")
        self.unit = HX711(self.config['gpio']['data'], self.config['gpio']['clock']) # Define the GPIO pins for the DATA and CLK of the HX711 breakout
        
        self.unit.set_reading_format("MSB", "MSB")

        print("info:Tare done! Add weight now...")

        # to use both channels, you'll need to tare them both
        #hx.tare_A()
        #hx.tare_B()
        #self.unit.set_gain(64)
        self.calibrate()
        self.connected = True
        self.start()
        return self
    
    
    def init_nau7802(self):
        # Create the bus
        print("Initialising NAU7802")
        self.bus = smbus2.SMBus(1) # Uses bus = 1 and i2C address = 42 is hardcoded into the NAU7802 chip

        # Create the scale and initialize it
        self.unit = PyNAU7802.NAU7802()
        if self.unit.begin(self.bus):
            #self.unit.setChannel(int(self.config["channel"]))
            #self.unit.setSampleRate(int(self.config["rate"]))
            #self.calibrate()
         
            print("Connected!\n")
        else:
            print("Can't find the scale, exiting ...\n")
            exit()
        
        return self
    



    def isConnected(self) -> bool:
        """
           Check whether the load cell is connected properly
           
        """
        isConnected = False # Default to false
        
        try:
            if self.config["amplifier"] == "HX711" :
                isConnected = self.unit.is_ready()
                return isConnected

            elif self.config["amplifier"] == "NAU7802":
                isConnected = self.unit.isConnected()
                return isConnected

        except BaseException:
            return isConnected


    def setSampleRate(self, rate):
        """
            Set the sampling rate of the load cell
            enum: (10 or 80Hz) for both amplifiers

        """
        
        if self.config["amplifier"] == "HX711" :
            print("Rate change not available for HX711 amplifier yet", flush=True)
            return self

        elif self.config["amplifier"] == "NAU7802":
            print("Setting sample rate for NAU7802 amplifier", flush=True)
            self.unit.setSampleRate(int(rate))
            isConnected = self.unit.isConnected()
            return self
        

        
    
    def tare(self):
        """
            Tare (zero) the load cell reading when there is no load applied to it
        """
        if self.config["amplifier"] == "HX711":
            self.unit.reset()
            self.unit.tare()
            
        if self.config["amplifier"] == "NAU7802":
            self.unit.reset()
            

        #elif self.config['type'] == "NAU7802":
        
        return self
        

    def calibrate(self, refunit=1):
        if self.config["amplifier"] == "HX711":
           
            # HOW TO CALCULATE THE REFERENCE UNIT
            # To set the reference unit to 1. Put 1kg on your sensor or anything you have and know exactly how much it weights.
            # In this case, 92 is 1 gram because, with 1 as a reference unit I got numbers near 0 without any weight
            # and I got numbers around 184000 when I added 2kg. So, according to the rule of thirds:
            # If 2000 grams is 184000 then 1000 grams is 184000 / 2000 = 92.
            #hx.set_reference_unit(113)
            
            self.unit.set_reference_unit(refunit)
            self.reset()
            self.tare()

        elif self.config["amplifier"]  == "NAU7802":
            #self.unit.calculateZeroOffset()
            self.unit.calibrateAFE()
        return self

    
    
    def reset(self):
        self.connected = False
        self.unit.reset()
        self.connected = True
            

        #elif self.config['type'] == "NAU7802"

        return self
    
    
    
    def start(self):
        """
            Thread to read loadcell values
        """
        self.connected = True
        t = Thread(target=self.update, args=[])
        t.daemon = True
        t.start()
        #print("Load Cell Started",flush=True)
        return self

    
    
    def stop(self):
        """ Stop loadcell reading """
        self.connected = False
        return self



    def update(self):

        while self.connected == True:
            try:
                if self.config["amplifier"] == "HX711":
                    val = self.unit.get_weight(5)/1000.0
                    
                if self.config["amplifier"] == "NAU7802":
                    try:
                        # Use one of these methods to read the load cell
                        #val = self.unit.getWeight() # kg
                        #Value in bits (0 - (2^24)-1)
                        #val = self.unit.getReading() # bits
                        val = self.unit.getAverage(5) # Average of n readings in bits
                        
                      
                        if val:
                            # Uses Felicity's statistical process control
                            self.readings.append(val)
                            self.mean_value = mean(self.readings)
                            self.stdev_value = stdev(self.readings)
                            
                            readings = np.array(self.readings)
                            readings = readings[ readings < self.mean_value + (2*self.stdev_value) ]
                            readings = readings[ readings > self.mean_value - (2*self.stdev_value) ]
                            
                            self.mean_value = mean(readings)
                            self.value_bits = self.mean_value
                        
                            # Value in grams
                            self.value_g = (float(self.value_bits) - float(self.config["calibration"]["zero_offset"]))/float(self.config["calibration"]["factor"])
                            # Value in Newtons
                            self.value_N = self.value_g  * 9.8066e-3
                            # Value in KiloNewtons
                            self.value_kN = self.value_N/1000.0 
                        
                            
                    except BaseException as err:
                        print("Update err: ", err)
                    
                  
                
                # Delay a short while to let the amplifier ADC stabilise
                #time.sleep(0.01)
            except BaseException as err:
                print("Load cell read error", err)
             
              
            #print(f"{self.value/1000.0:.3f}",flush=True)
       
    def setChannel(self, channel:int) -> bool:
        if self.config["amplifier"] == "HX711" :
            print("setChannel: not available for HX711 amplifier yet", flush=True)
            return False

        elif self.config["amplifier"] == "NAU7802":
            print(f"Setting NAU7802 amplifier to channel: {channel}", flush=True)
            if channel == 1:
                ret = self.unit.setChannel(0)
            if channel == 2:
                ret = self.unit.setChannel(1)
            return ret


    def read(self):
        return self.value



    def exit(self):
        GPIO.cleanup()
        sys.exit()
        
        


if __name__ == "__main__":
    # If we are running this script as a standalone program for debugging...
    # Start the extensometer
    lc = LoadCell().init()
    lc.start()
    while True:
        # Read continuously at about 20Hz (using time.sleep(0.05))
        print(lc.read(), flush=True)
        # Delay a short while until the next read event
        time.sleep(0.05)
