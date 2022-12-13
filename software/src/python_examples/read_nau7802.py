import PyNAU7802 # Amplifier 2 - i2c
import smbus2
import time


scale = PyNAU7802.NAU7802()
bus = smbus2.SMBus(1)

# For 50kg load cell
zero_offset = 7200
linear = 67.3 # converts bits to grams

zero_weight = 1752.91 # Weight of top clamp with all the gubbins install on it

# For 1000kg load cell
# No values calibrated

if scale.begin():
    
    scale.setGain(32)
    
    while True:
        reading = scale.getReading()
        calibrated = (-(reading-zero_offset)/(linear)) - zero_weight
        print(reading, calibrated)
        time.sleep(0.2)
