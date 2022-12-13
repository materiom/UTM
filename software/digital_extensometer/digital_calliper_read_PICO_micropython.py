from machine import Pin
import time
import micropython
micropython.alloc_emergency_exception_buf(100)

def decode(Pin):           #defining interrupt handling function
    global position
    global idx
    global current_position
    global t_last_bit
    global reading_start
    global t_current_bit
    global velocity
    global bitArray
    
   
    data_value = data.value()
    t_current_bit = time.ticks_us()
    delta = t_current_bit - t_last_bit
    t_last_bit = t_current_bit
    #print(idx, delta, data_value, position)
   
    
    if delta > 5000 or idx > 23:
        # We have reached the end of the position clock bits OR position is unfeasibly large
        # RESET everything
        idx = 0
        position = 0
        bitArray = []
    
    
    if idx < 20 : # For the first 20 clock pulses 
        if data_value == 1: # If the data bit is high do this
            position += 2**idx # Add the next positive bit to the position
            #bitArray.append(1)
            
        #else:
            #bitArray.append(0)

            
            
    elif idx == 20: # This is the 'sign' clock pulse
        if data_value == 1: # If the data bit is positive here it means the calliper position should be negative
            position = -1 * position # Make the position negative
            #bitArray.append(1)
        #else:
            #bitArray.append(0)
    
    elif idx == 23: # 24th bit is the last on in the sequence
        delta_t = reading_start - t_last_bit
        position = position*10 # Send position in microns
        delta_d = current_position - position
        velocity = int(abs(delta_d*1e6/delta_t)) # Velocity in microns per second
        #print(bitArray)
        print(f"{position} {velocity}") # Print out the position, formatted to 2 decimel places as per the calliper LCD read out
        current_position = position
        reading_start = t_current_bit
    
    
    idx += 1
        



led = Pin(17, Pin.OUT)
data = Pin(3, Pin.IN) # Initialise the data pin (GP3 on the Pico, pin 5 on the pinout map)
data_out = Pin(26, Pin.OUT)
idx = 0 # Initialise the bit index
position = 0 # Initialise the position
velocity = 0
interrupt = Pin(2,Pin.IN)   # setting GP2 PIR_Interrupt as input
interrupt.irq( trigger = Pin.IRQ_RISING, handler = decode) # Define the interrupt to only occur on the rising edge of the clock line     

t_last_bit = time.ticks_us()
reading_start = 0
t_current_bit= 0
current_position = 0.0
delay = 0.5
bitArray = []

while True:
    pass
    
    
        
        
        
        
        
        