import time
import smbus2 as smbus
from threading import Thread
import struct # to convert values into bytes ready to send over hi2c


import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)


def mapFloatRangeToInt(value:float, inMin:float, inMax:float, outMin:int, outMax:int) -> int:
    inRange = inMax-inMin
    outRange = outMax - outMin
    scaled = float(value - inMin) / float(inRange)
    return int(outMin + ( scaled * outRange ))



def scalePercentTo16bit(value: float) -> int:
    """
        value = 0.0-100.0% float value
        return 0-65535 int value
    """
    #print("Input", value)
    if value >= 100.0:
        return 65535
    elif value <= 0.0:
        return 0
    else:
        bitVal = mapFloatRangeToInt(value, 0.0, 100.0, 0, 65535)
        #print("Output", bitVal)
        return bitVal
 


class Motor:
    def __init__(self):
        self.setpoint = 0 # Speed setpoint 0-65535 value
        self.speed = 0 # Current speed
        self.direction = 0  # 0 = disable, 1 = Tension, 2 = Compression
        self.current = 0
        self.jog_value = 0 # Job potentometer value (10bit 0-1023)
        self.led1 = 0 # LED1 brightness (16bit 0-65535)
        self.led2 = 0 # LED2 brightness (16bit 0-65535)
        self.jog = False # Flag to test if the machine is moving during a jog procedure
        self.running = False # Flag to check if the motor is both activated AND running
        self.connected = True # Flag to check if the motor is active and can be communicated with (via Arduino Micro Pro)
        self.stalled = False # activated if current > 0 and speed == 0
        self.enabled = False # flag to check if the motor is enabled - Safety feature
        self.ard_addr = 0x0a # I2C bus address (type the address i2cdetect -y 1 functions shows) 
        self.bus = smbus.SMBus(1) # indicates /dev/ic2-1
    
        GPIO.setup(27,GPIO.OUT) # LED for Enable status Active as OUTPUT
    
    def init(self, config=None):
        """
         Reinitialises the motor connection
        """
        
        self.connected = True # Flag to check if the motor is active and can be communicated with (via Arduino Micro Pro)
        t = Thread(target=self.start, args=[])
        t.daemon = True
        t.start()
        return self


    def enable(self):
        try:
            self.enabled = True
            #GPIO.output(27,GPIO.HIGH) # LED for Enable status ON
            return 1 # Return 1 to the controller to say that it has been enabled
        except BaseException as err:
            return 0 # Return 0 to show the controller that the enabling process hasn't worked
    
    
    def disable(self):
        try:
            self.stop()
            self.setpoint = 0
            self.enabled = False
            #GPIO.output(27,GPIO.LOW) # LED for Enable status OFF
            return 0
        except BaseException as err:
            return 1 # Return 0 to show the controller that the disabling process hasn't worked
    
        
    
    
    def start(self):
        """
        Start the motor turning with the initial settings provided
        """
        #self.connected = True
        
        print("info: Starting motor\n")
        if not self.enabled:
            print("info:Motor is disabled. Enable it with the 'enable' command")
        while True:
            self.update()
           
        return self
    
    
    def update(self):
        # Constantly provide values to the Arduino as a kind of heartbeat so
        # that it knows the Pi is still alive
        self.writeI2C()
        time.sleep(0.001)
        # Read the resultant values in the Arduino
        self.readI2C()
        #time.sleep(0.01)
       

        return self


    def stop(self):
        """
        Stop the motor turning 
        """
        
        self.direction = 0
      
        self.is_running = False
        print("info:motor:Stopped")

        return self



    def halt(self):
        """
        Start the motor turning with the initial settings provided
        """
        print("info:motor:Halted")
        self.disable()

        return self



    def set_led(self, num:int, val:float):
        """
            updates led brightness
        """
        # map the input values to 0-65535
        bitVal = scalePercentTo16bit(val)
        
        if num == 1:
            self.led1 = bitVal
            print(f"LED1 brightness changed: {self.led1}")
        if num == 2:
            self.led2 = bitVal
            print(f"LED2 brightness changed: {self.led2}")
            
        return self
    
    
    def set_speed(self, val:float):
        """
            updates the speed setpoint
            writes the new speed to the Arduino Pro Micro
        """
        # map the input values to 0-65535
        bitVal = scalePercentTo16bit(val)
        
        self.setpoint = bitVal
        #print(f"Motor setpoint: {self.setpoint}")

        return self



    def set_direction(self, val:int):
        """
            updates the motor direction
            writes the new direction to the Arduino Pro Micro
        """
        
        if val == 0:
            self.stop()
        elif val == 1:
            self.direction = 1
        elif val == 2:
            self.direction = 2
    
        return self



    def convert2bytes(self, src):
        """
        convert values to bytes to send to be written
        """
        converted = []
        for b in src:
            print(b)
            converted.append(ord(b))
        return converted
    
    
    
    def writeI2C(self, cmd=None):
        """
        send updated values to the Arduino Pro Micro
        Need to await an acknowledgement to check the update has been recieved
        use self.read() for this
        
        A command is built up of 3 bytes, transmitted as an array.
        The first byte identifies the value to change.
        The second 2 bytes are a 16 bit Unsignedint variable, split up e.g. as per the tutorial below

        First byte 0 - Select motor direction (0 = Motor output disable, 1 = Tensile, 2 = Compression)
        First byte 1 - Set required tacho pulses per minute (0-65535, seems plausible for integer math in the Pi loop for the moment)
        First byte 2 - Set LED 1 brightness (0-65535, 16bit PWM)
        First byte 3 - Set LED 2 brightness (0-65535, 16bit PWM)
        First byte 4 - Data return format (0 = shortened, 1 = full)

        """
        
        try:
            if cmd == None:
                # base command to constantly write values to the arduino
                data = [self.direction, self.setpoint, self.led1, self.led2, 1]
                # B = 8bit integer
                # H = 16bit integer
                self.bus.write_i2c_block_data(self.ard_addr, 0, struct.pack('!BHHH', self.direction, self.setpoint, self.led1, self.led2))
                #print(f"Setpoint =>\t :  Dir {data[0]} \t Speed: {data[1]}\t LED1: {data[2]}\t LED2: {data[3]}\t dframe: {data[4]}")
            
            else:
                cmd = self.convert2bytes(cmd)
                print(cmd)                
                self.bus.write_byte(self.ard_addr, cmd )
            self.connected = True
        except OSError as err:
            #print("error:I2C failed to write to Arduino")
            #self.is_connected = False
            pass
    
        return self


    def readI2C(self):
        """
        recieve acknowledgements and updated values from the Arduino Pro Micro

        Read acknowledegments will be of the form of:
        4 bytes containing 2 Unsignedint variables
            
        1. Current tacho pulses per minute - applicable to all operation modes
        2. Current motor current reading - applicable to all operation modes
        3. Jog pot value (Only in full frame communication format)

        Present tacho pulses per minute is 0-65535
        Present motor current reading is 0-1023 (10bit ADC conversion)
        Manual jog pot value is 0-1023 (10bit ADC conversion)


        """

        try:
            data = self.bus.read_i2c_block_data(self.ard_addr, 0, 6) # expected 3 * 16bit () integers to read
            #print(data)
            data = struct.unpack("!HHH", bytearray(data))
            #print(f"Actual =>\t Speed: {data[0]} \t Motor Current: {data[1]}\t Motor Jog: {data[2]}\n")
            self.speed = int(data[0])
            self.current = int(data[1])
            self.jog_value = int(data[2])
            
            if self.speed > 0 and self.current > 0:
                self.running = True
                
            if self.speed == 0 and self.current > 0:
                self.stalled = True
                
            if self.speed == 0 and self.current == 0:
                self.running = False
         
            
            if self.jog_value > 0:
                self.jog = True
            else:
                self.jog = False
            
            #print(f"Recieve from Arduino: {data}\n")
            
        except BaseException as err:
            #print("error:Remote read error\n")
            # Should probably halt the test if this fails
            self.connected = False

            #self.stop()
            pass



        return self





