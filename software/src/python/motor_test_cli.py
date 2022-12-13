"""
This script is used for testing the motor control without the need for the controller.py script
or a more complex GUI

Use:
Make sure that this script is in the same folder as the motor.py script.
motor.py contains the Motor class that is used to communicate with the Arduino
that controls the UTM motor via I2C

The Arduino will also need to be running the i2c_test.ino script in the "../Arduino/" folder 

run with: > python3 motor_test_cli.py

Input further commands when prompted

Example commands:

- Set speed to 30000 (0-65535 resolution)
> speed:30000


- Set motor direction = 2 (0=off, 1=CW, 2=CCW)
> dir:2

- turn motor off (also sets speed to 0)
> dir:0

- Turn LED1 on with brightness of 50000 (0-65535 resolution)
led:1:50000

- Turn LED2 off
led:2:0


"""


import time
import smbus2 as smbus 
from motor import Motor

if __name__ == "__main__":
    mo = Motor().init()
    while True:
        cmd = input("Enter motor command and press Return:\n")
        if cmd:
            try:
                cmd = cmd.split(":")
                if cmd[0] == "enable":
                    mo.enable()
                    print(f"CMD to write to Arduino: {cmd}")
                elif cmd[0] == "disable":
                    mo.disable()
                    print(f"CMD to write to Arduino: {cmd}")
                elif cmd[0] == "speed":
                    mo.set_speed(int(cmd[1]))
                    print(f"CMD to write to Arduino: {cmd}")
                elif cmd[0] == "dir":
                    mo.set_direction(int(cmd[1]))
                    print(f"CMD to write to Arduino: {cmd}")
                elif cmd[0] == "led":
                    mo.set_led(cmd[1], cmd[2])
                    print(f"CMD to write to Arduino: {cmd}")
                else:
                    print("Sorry, command not recognised. Please try again...")
                
                time.sleep(0.5)
                mo.readI2C()
                
                print(f"Setpoint: {mo.setpoint}, Speed: {mo.speed}, Direction: {mo.direction}\n")
            except BaseException as err:
                print(err)


