import time
import json
import struct
from threading import Thread
import socket
import math
import zmq
from collections import deque

from data_logger import Logger # Used to manage the data logging for the test
from test import BasicTest # used to define the Test procedure
from load_cell import LoadCell
from motor import Motor
from digital_extensometer import Extensometer
from camera import VideoExtensometer

from simple_pid import PID

def mapFloatRangeToInt(value:float, inMin:float, inMax:float, outMin:int, outMax:int) -> int:
    inRange = inMax-inMin
    outRange = outMax - outMin
    scaled = float(value - inMin) / float(inRange)
    return int(outMin + ( scaled * outRange ))





class Controller:
    
    def __init__(self, config=None):
        
        ## Everything has been moved to the init()
        ## Method so it can be recalled to reload the system
        ## when the configuration is changed
        
        
        
        
        
        return None

    def init(self, config=None):
        """
            Initialises the controller's main thread
            It starts the run() function in a separate thread
        """
        if config == None:
            f = open("./config/user.db","r")
            #f = open("../../config/default.db", "r")
            self.config = json.load(f)
            #print(self.config)
        
        
        
        self.zmqCtx = zmq.Context()
        self.sockets = { "pub":  self.zmqCtx.socket(zmq.PUB), "sub":  self.zmqCtx.socket(zmq.SUB) } 
        

        
        self.control_loop_time = 0.01 # 100 Hz
        
        self.is_running =  False
        
        self.logger = Logger(self.config["logging"], self.sockets["pub"], debug=False) # define the logger config, debug=True to output all data even if not running a test
        self.logger.init()

        self.load_cell =  LoadCell(self.config["modules"]["load_cell"]) # Load the LoadCell with its default config
        self.load_cell.init()
        
        self.extensometer =  Extensometer(self.config["modules"]["digital_extensometer"]) # Load the Extensometer with the default config
        self.extensometer.init()
        
        
        
        self.video_extensometer = None
        #self.video_extensometer =  VideoExtensometer(self.config["modules"]["video_extensometer"]) # Load the Extensometer with the default config
        self.video_extensometer =  VideoExtensometer() # Load the Extensometer with the default config
        self.video_extensometer.start()
        
        """
        try:
            self.video_extensometer.init()
        except BaseException as err:
            self.emit_alarm("Video Extensometer failed to start")
        """
        
        self.displacement_offset = 0.0
        
        self.load_bits_offset = 0
        self.load_g_offset = 0.0
        self.load_N_offset = 0.0
        self.load_kN_offset = 0.0
        
        ## Define some setpoints for PID control if are using it.
        self.speed_setpoint = 0.0
        self.position_setpoint = 0.0
        self.force_setpoint = 0.0
        
        self.jog_mode = "slow" # slow or fast
        
        # Load empty test.
        # This will eventually be fed a test dict to define what it will do
        # To feed the test a new config, use the test.init({test_dict}) method
        self.test = BasicTest(self, logger=self.logger) # Send the data logger object to be used by the test 
        
        
        
        # Initialise the PI (not D) controller for speed
        #self.speed_pid = PID(float(self.config["controller"]["pid"]["kp"]), float(self.config["controller"]["pid"]["ki"]), float(self.config["controller"]["pid"]["kd"]), setpoint=0)
        self.speed_pid = PID( 0.5, 0.2 , 0.01)
        self.speed_pid.output_limits = (20, 100)
        self.speed_pid.sample_time = self.control_loop_time
        
        self.sr_pid = PID( 0.5 , 0.2 , 0.01)
        self.sr_pid.output_limits = (20, 100)
        self.sr_pid.sample_time = self.control_loop_time
        
        self.force_pid = PID( 0.5 , 0.2 , 0.01)
        self.force_pid.output_limits = (20, 40) # Reduce the potential output speeds that can be set for force control
        self.force_pid.sample_time = self.control_loop_time
        
        
        self.data_q = deque(maxlen=50) # Deque queue to store previous data values in a circular buffer

        
        self.data = {
            "time": 0.0,
            "displacement_abs" : 0.0,
            "displacement_rel" : 0.0,
            "displacement_video": 0.0,
            "sample_length": 0.0,
            "speed" : 0.0,
            "speed_setpoint": 0,
            "load_bits_abs": 0.0,
            "load_bits_rel": 0.0,
            "load_g_abs": 0.0,
            "load_g_rel": 0.0,
            "load_N_abs": 0.0,
            "load_N_rel": 0.0,
            "load_kN_abs": 0.0,
            "load_kN_rel": 0.0,
            "strain_eng": 0.0,
            "strain_true": 0.0,
            "strain_rate": 0.0,
            "stress_eng": 0.0,
            "stress_true": 0.0,
            "motor_direction":0,
            "motor_setpoint": 0,
            "motor_speed": 0,
            "led1_brightness": 0,
            "led2_brightness":0,
            "motor_current": 0.0,
            "motor_speed":0,
            "motor_jog": 0,
            "ismoving": 0,
            "active_section": {
                        "name": "Idle",
                        "direction": 0, 
                        "setpoint": -1,  
                        "control": -1,
                        "end": -1,
                        "input": False,
                        "delay": 0
                     }
        }
        

        
       
        
        try:
            self.load_cell.start() # Start the load cell reading
        except:
            self.sockets["pub"].send("alarm:Load Cell failed to start".encode("utf8"))
        
        try:
            self.extensometer.start() # start the extensometer reading
        except:
            self.sockets["pub"].send("alarm:Extensometer failed to start".encode("utf8"))
        
        
        ## Initialise the actuator motor 
        self.motor = Motor()
        self.motor.init()
        
        time.sleep(1)

        self.status = {
            "enabled": self.is_enabled(),
            "controller": self.is_running, 
            "motor": self.motor.connected,
            "motor_running": self.motor.running, 
            "load_cell" : self.load_cell.connected, 
            "digital_extensometer" : self.extensometer.connected,
            "video_extensometer": self.video_extensometer.connected,
            "test_running": self.test.is_running,
            "test_paused": self.test.is_paused,
            "jog_mode": self.jog_mode
            }
        
        ## Send status to the frontend
        self.emit_status()

        
        self.sockets["sub"].connect('ipc://pub.ipc') # Socket path in relation to the Electron app. NOT this script
        self.sockets["sub"].subscribe("")
        self.sockets["pub"].bind('ipc://sub.ipc') # Socket path in relation to the Electron app. NOT this script
        
     
     
        t0 = Thread(target=self.stream_status, args=[])
        t0.daemon = True
        t0.start()
     
        
        t1 = Thread(target=self.listen_socket, args=[])
        t1.daemon = True
        t1.start()
        
        
        
        # Start the data streaming thread
        # NECESSARY in order to send data to the GUI
        # or send to any remote monitoring system
        self.stream_start()
        
        
        t2 = Thread(target=self.run, args=[])
        t2.daemon = True
        t2.start()
        
       
          
        t3 = Thread(target=self.get_data, args=[])
        t3.daemon = True
        t3.start()
        
        self.emit_status()
        
        
        return self
        
        
        
        
    def listen_socket(self):

        while True:
            try:
                msg = self.sockets["sub"].recv()
                msg = msg.decode("utf8")
                self.process_cmd(msg)
            
            except zmq.ZMQError as e:
                #print(e.errno, flush=True)
                if e.errno == zmq.ETERM:
                    break 
        
        
    
    
    
    
    
    def process_cmd(self, msg):
        """
            this function deals with the incoming socket messages to control the UTM machine
        """
        try:
            m = msg.split(":") # Split the message in to and array using the delimiter ":" as per the UTM protocol
            #print(m,flush=True)
            
            
            if m[0] == "config":
                if m[0] == "reload":
                    ## A request to reload the config and restart the controller
                    self.emit_event("controller", "Config changed. Controller reinitialised")
                    self.init()
            
            
            
            if m[0] == "mode":        
                if m[1] == "jog":
                    self.set_jog_mode(m[2])
            
            
            
            
            
            
                     
            if m[0] == "cmd": 
                #self.sockets["pub"].send("cmd sent to controller".encode("utf8"))
                
                if m[1] == "enable":
                    self.enable()
                
                elif m[1] == "disable":
                    self.disable()
                
                
                elif m[1] == "jog":
                    self.jog_actuator(int(m[2]))
                    
                elif m[1] == "speed":
                    self.set_actuator_speed_setpoint(float(m[2]))
                    
                elif m[1] == "position":
                    self.set_actuator_position_setpoint(float(m[2]))
                    
                    
                elif m[1] == "dir":
                    self.set_actuator_direction(int(m[2]))
                    
                elif m[1] == "led":
                    self.set_led_brightness(int(m[2]), float(m[3]))
                
                elif m[1] == "init":
                     if m[2] == "digital_extensometer" or m[2] == "video_extensometer" or m[2] == "load_cell" :
                        self.reload_subsystem(m[2])
                        
                elif m[1] == "zero":
                    if m[2] == "digital_extensometer" or m[2] == "load_cell":
                        self.zero_sensor(name=m[2])
                
            elif m[0] == "status":
                # A Request for modules statuses
                self.emit_status()
                

            elif m[0] == "test":
                # Commands to control a test
                if m[1] == "start":
                    if m[2]:
                        self.start_test(m[2])
                elif m[1] == "pause":
                    self.test.pause()
                elif m[1] == "resume":
                    self.test.resume()
                elif m[1] == "stop":
                    self.stop_test()
                
        
        except BaseException as err:
            print(err, flush=True)
            self.emit_alarm("Command not accepted")
            
    
        return self
        
        
    def emit_alarm(self, message):
        self.sockets["pub"].send(json.dumps({"type":"alarm", "message": f"{message}", "time": time.time() }).encode("utf8"))
        
    
    def emit_status(self):
        ## Emit the status of modules to the frontend
        if not self.test.test is None:
            test_id = self.test.test["_id"]
        else:
            test_id = ""
        
        self.status["enabled"] = self.is_enabled()
        self.status["controller"] = self.is_running
        self.status["motor"] = self.motor.connected
        self.status["motor_moving"] = self.motor.running
        self.status["load_cell"] = self.load_cell.connected 
        self.status["digital_extensometer"] = self.extensometer.connected
        self.status["video_extensometer"] = self.video_extensometer.connected
        self.status["test_running"] = self.test.is_running
        self.status["test_paused"] = self.test.is_paused
        self.status["test_id"] = test_id
        self.status["test_status"] = self.test.status
        self.status["jog_mode"] = self.jog_mode
            
            
        message = {
            "type": "status",
            "message" : self.status,
            "time": time.time()
        }
        self.sockets["pub"].send(json.dumps(message).encode("utf8"))
        

    def emit_event(self, system:str, message:str, reason=None):
        ## Emit an event to the frontend
        
        if not reason is None:
            reason = ""
        
        self.sockets["pub"].send(json.dumps({"type":"event", "system":system ,"message": message, "reason":reason, "time": time.time() }).encode("utf8"))
    
    
       
    
    
    
    def start_test(self, test_id):
        # Stop the data logger if it is running in debug mode
        self.logger.stop()
        

        # Get the test json info from the nedb database
        with open(f"./data/{test_id}.json","r") as f:
            
            testinfo = json.load(f) # provides a json array of ALL the values
            
        
        
        self.test.init(test=testinfo)
        # test.init() will reinitilise the data logger with the corret test_id
        # self.test.init() will create a test.
        # now we need to start the test! 
        
        time.sleep(5) ## Delay before the test starts in case the user wants to back out and cancel the test

        
        # Auto zero the scales
        self.zero_sensor("load_cell", True) # True to force the zeroing process
        self.zero_sensor("digital_extensometer", True) # True to force the zeroing process
        
        self.emit_event("test", "start")
        
        time.sleep(1) ## Delay before the test starts in case the user wants to back out and cancel the test

        
        ret = self.test.start()
        self.enable() # Enable the controller
        
        self.emit_event("test", "start")
       
        # let the frontend know what is going on
        self.emit_status()
        # now the magic happens!!! Hopefully
        
        
        
    
    def stop_test(self):
        """
            Stop the test and make sure the machine is halted for safety
        """
        print("STOPPING Test from controller", flush=True)
        self.test.stop()
        self.emit_event("test", "stop")
        
       
    
    def finish_test(self, message=None):
        """
            Stop the test and make sure the machine is halted for safety
        """
        self.halt()
        self.emit_status()
        if not message is None:
            self.emit_event("test", "finished", message)
        else:
            self.emit_event("test", "finished")
    
       
    def get_data(self):
        # Read ALL the data and update the data array for the next loop

        while True:
            self.data["time"] = time.time()
            self.data["displacement_abs"] = self.extensometer.displacement
            self.data["speed"] = self.extensometer.speed
            self.data["displacement_rel"] = self.data["displacement_abs"] - self.displacement_offset 
            
            self.data["load_bits_abs"] = -self.load_cell.value_bits # Look out for the negative sign here
            self.data["load_g_abs"] = -self.load_cell.value_g # Look out for the negative sign here
            self.data["load_N_abs"] = -self.load_cell.value_N # Look out for the negative sign here
            self.data["load_kN_abs"] = -self.load_cell.value_kN # Look out for the negative sign here
            
            self.data["load_bits_rel"] = self.data["load_bits_abs"] - self.load_bits_offset
            self.data["load_g_rel"] = self.data["load_g_abs"] - self.load_g_offset
            self.data["load_N_rel"] = self.data["load_N_abs"] - self.load_N_offset
            self.data["load_kN_rel"] = self.data["load_N_rel"] / 1000.0
            
            
            self.data["motor_direction"] = self.motor.direction
            self.data["motor_setpoint"] = self.motor.setpoint
            self.data["motor_speed"] = self.motor.speed
            self.data["led1_brightness"] = self.motor.led1
            self.data["led2_brightness"] = self.motor.led2,
            self.data["motor_current"] = self.motor.current
            self.data["motor_jog"] = self.motor.jog_value
            
            self.data["displacement_video"] = self.video_extensometer.p_dist
  
            self.data["speed_setpoint"] = self.speed_setpoint
            time.sleep(0.005)

        return self

        
    def run(self):
        """
            runs the controller in a loop
        """
        
        print("info:Controller run called")
        self.is_running = True
        
        # Start the data logger
        # If *kwarg debug=True then it will log EVERYTHING from now until the software is closed
        self.logger.start() 
        
        self.speed_pid.setpoint = 0.0 # mm/s speed control

        
        while True: # Run in an infinite loop
            
            # This loop is the main control loop
            # It runs as fast as possible
            
            # do some basic checks on the subsystems
            #self.is_reading = self.load_cell.is_reading and self.extensometer.is_reading #and self.motor.is_connected
            
            # Halt the motor and call an error if any of the subsystems are uncontactable
            #self.is_running = self.is_reading
            
            
            # ALL LIVE DATA is being constantly updating in a separate thread (t3) in the init function
            

            # CHECK SAFETY LIMITS and call an immediate halt if anything is over or under the limits
            
            if self.motor.enabled: # Only enter this loop if the Motor is enabled
                
                # ensure the data logger is enabled to store data to the csv file
                self.logger.isLogging = True
                
                
                
                ####
                ##  SAFETY CHECKS
                ####
                ## Perform safety checks if the motor is enabled
                self.check_limits() # function disables the motor itself if a limit is breached
                
                

              
              
              
                #####
                #
                # RUNNING A TEST
                # Now we do some stuff if we are running a test
                #
                ##### 
                
                if self.is_running and self.test.is_running: # check if we are running an active test
                    """ We have an active test running so we do some extra things to control the test """
                    
                    #print(self.test.is_running, flush=True)
                    
                    # Send this controller data to the test
                    # The TEST class will then use this data to check where in the test protocol/method it is at
                    # The TEST class updates the required setpoints itself and will stop itself if it
                    # has reached the required endpoint/
                    #self.test.data = self.data
                    
                    
                    
                    # Current sample length = initial sample length + relative displacement
                    self.data["sample_length"] =  float(self.test.sample["gauge"]["len"]) + self.data["displacement_rel"]
 

                    # Calculate ENGINEERING STRAIN and TRUE STRAIN
                    self.data['strain_eng'] = (abs(self.data["displacement_rel"]) ) / float(self.test.sample["gauge"]["len"])

                    self.data['strain_true'] = math.log( 1 + self.data["strain_eng"])


                    # Calculate STRAIN RATE - needs at least two data points to do this
                    if len(self.data_q) >= 2:
                        strain_0 = self.data['strain_eng'] # Current strain
                        time_0 = self.data['time'] # Time now (for this loop at least)
                        strain_1 = self.data_q[-2]["strain_eng"] # Previous strain value
                        time_1 = self.data_q[-2]["time"] # Previous time
                        delta_t = time_0 - time_1
                        
                        if delta_t > 0:
                            self.data['strain_rate'] = ( strain_0 - strain_1 ) / ( time_0 - time_1 )

                

                    # Calculate ENGINEERING STRESS
                    self.data['stress_eng'] = self.data["load_N_rel"] / float(self.test.sample["gauge"]["cross_section_area"])
                    
                    # Placeholder until I can do something better
                    self.data["stress_true"] = self.data["stress_eng"]


                    # Write new values to the test and get feedback as to whether we need to switch
                    # to the next stage in the test procedure. This will result in setting new setpoints
                    self.data["active_section"] = self.test.sections[self.test.active_section]
                    self.test.data = self.data # This is needed again as we have just updated all the data
                    
                    # Get any updated setpoints from the TEST class
                    setpoints = self.test.get_setpoints()
                    #print(setpoints, flush=True)
                    self.set_actuator_direction(setpoints["direction"])
                    
                    
                    
                    self.test.check_progress() # This function also expects to find some user input somewhere but if I simply call input() it might block something...so this functionality is not completed

                    # this will be running all the time ready for if we want to start a test
                    # Maybe a nice circular deque buffer would be good to store everything?

                    #self.data_q.append(self.data) # Append data to the queue

                    ####
                    ##   PID CONTROL LOOP CALCULATIONS
                    ####
                    
                    
                    # PID type will need to change based on the control type in the TEST method
                    pid_type = setpoints["type"]
                   
                    
                    if pid_type == "speed":
                        self.speed_pid.setpoint = setpoints["speed"] # mm/s speed control
                        new_spt = self.speed_pid(float(self.data["speed"])) # Run the control algorithm to get speed to the setpoint mm/s - this outputs 0-100 to the motor, which then converts it to 0-65535 16bits.
                        #new_spt = mapFloatRangeToInt(new_spt, 0, 100, 0, 65535) # Convert the 0-100 value to 0-65535 16bit value to send to the motor
                        #print(new_spt, flush=True)
                      
                    if pid_type == "strainrate":
                        self.sr_pid.setpoint = setpoints["strainrate"] # mm/s speed control
                        new_spt = self.sr_pid(float(self.data["strain_rate"])) # Run the control algorithm to get speed to the setpoint mm/s - this outputs 0-100 to the motor, which then converts it to 0-65535 16bits.
                        #new_spt = mapFloatRangeToInt(new_spt, 0, 100, 0, 65535) # Convert the 0-100 value to 0-65535 16bit value to send to the motor
                        #print(new_spt, flush=True)
                        
                    if pid_type == "load":
                        self.force_pid.setpoint = setpoints["load"] # mm/s speed control
                        new_spt = self.force_pid(float(self.data["load_N_rel"])) # Run the control algorithm to get speed to the setpoint mm/s - this outputs 0-100 to the motor, which then converts it to 0-65535 16bits.
                        #new_spt = mapFloatRangeToInt(new_spt, 0, 100, 0, 65535) # Convert the 0-100 value to 0-65535 16bit value to send to the motor
                        #print(new_spt, flush=True)
                        
                        
                    # Update the motor speed based on the new setpoint value
                    self.set_actuator_speed(new_spt)


                else:
                    self.speed_pid.setpoint = 0.0 # mm/s speed control


              

                self.logger.update(self.data) # update the values stored by the data logger
            
            else:
                #disable the data logger - the csv file will remain open and ready though
                self.logger.isLogging = False
            
           
          
            time.sleep(self.control_loop_time)
                
                
        ## Halt everything if we come out of this while loop as we wont
        ## be able to control anything properly
        self.halt()



    def stream_start(self):
        """ Threading to stream data values """
        self.is_reading = True
        t = Thread(target=self.stream, args=[])
        t.daemon = True
        t.start()
        return self
    

    def stream(self):
        """
            function to stream result outside of this controller script
            ie to the GUI
        """
        
        while True:
            data = {"type":"data", "data": self.data}
            jdata = json.dumps(data) # Convert dict into a json string to send to the front end
            #print(jdata, flush=True)
            self.sockets["pub"].send(jdata.encode("utf8"))
            
            time.sleep(0.1)
    
        return self
    
    
    
    def zero_sensor(self, name=None, force=False):
        """ Zero the relative sensor value defined by 'name' """
        
        # Do nothing if name is not supplied or if the test is currently running
        if not name is None and (not self.test.is_running or force == True):
            if name == "load_cell":
                self.load_bits_offset = self.data["load_bits_abs"]
                self.load_g_offset = self.data["load_g_abs"]
                self.load_N_offset = self.data["load_N_abs"]
            if name == "digital_extensometer":
                self.displacement_offset = self.data["displacement_abs"]
                
        return self
    
    
    
    def set_led_brightness(self, num:int, val:float):
        """
            updates led brightness
        """
        self.motor.set_led(num, val)
        return self
    
    
    
    def go_to_position(self, val:float):
        """
            Make the 
        """
        
        self.test.go_to_position(val)
    
    
    
    def set_actuator_speed_setpoint(self, val:float):
        """
            updates the speed setpoint
            val = 0.0-2.0 mm/s float values
        """
        self.speed_setpoint = val

        return self
        
        
    
    
    def jog_actuator(self, val:int):
        """
            updates the speed setpoint
            val = 0.0-2.0 mm/s float values
        """
       
            
        if self.is_enabled() == True:
            self.set_actuator_direction(val) # set jog direction
            if self.jog_mode == "slow":
                self.set_actuator_speed(30) # 30% jog speed
            elif self.jog_mode == "fast":
                self.set_actuator_speed(100) # 100% jog speed
            
           
        else:
            self.emit_alarm("System not enabled. Cannot perform jog action.")

        return self
   
    
    def set_jog_mode(self, mode:str):
        """
            Set the max speed of jog mode
        """
        if mode == "slow" or mode == "fast":
            self.jog_mode = mode
       
        return self.jog_mode
        
        
    def set_actuator_position_setpoint(self, val:float):
        """
            updates the position setpoint
            val = -30.0 to 220.0 mm float values
        """
        self.position_setpoint = val

        return self
        
        
        
        
    def set_actuator_speed(self, val:float):
        """
            updates the speed setpoint
            writes the new speed to the Arduino Pro Micro
            val = 0.0-100.0 (%) float values
        """
        self.motor.set_speed(val)
        return self




    def set_actuator_direction(self, val:int):
        """
            updates the motor direction
            0 = STOP
            1 = Compression
            2 = Tension
            writes the new direction to the Arduino Pro Micro
            val = 0,1,2 - integer values
        """
        if val == 0:
            self.set_actuator_speed(0)
            
        self.motor.set_direction(val)
        
        return self
        
        
        
        
        
    def reload_subsystem(self, system:str):
        
        if system == "digital_extensometer":
            print("Reinitialising Extensometer", flush=True)
            self.extensometer.stop()
            self.extensometer.init()
            self.extensometer.start()
            
        if system == "load_cell":
            print("Reinitialising Load Cell", flush=True)
            self.load_cell.stop()
            self.load_cell.init()
            self.load_cell.start()
            
        if system == "video_extensometer":
            print("Reinitialising Video Extensometer", flush=True)
            self.video_extensometer.stop()
            self.video_extensometer.init()
            self.video_extensometer.start()
        
        
        
        
    def is_enabled(self):
        return self.motor.enabled
    
    
    def enable(self):
        # Enable the system
        print("Enabling the controller", flush=True)
        self.emit_event("controller", "Enabling motor")
        
        res = self.motor.enable()
        self.status["enabled"] = res
        return self
    
    
    
    
    def disable(self):
        # Disable the system
        print("Disabling the controller", flush=True)
        self.emit_event("controller", "Disabling motor")
        res = self.motor.disable()
        
        self.data["enabled"] = res
        print(res, self.data["enabled"], flush=True)
        return self
        

    def stream_status(self):
        while True:
            self.emit_status()
            time.sleep(1)



    def check_limits(self):
        """ Checks all the current data vs the configured safety limits """
        
        # Check load
        load_check = False
        disp_check = False
        motor_check = False
        
        if self.data["load_N_abs"] > float(self.load_cell.limits[1]):
            print(f"alarm:load_cell:Load cell over HIGH limit: {self.data['load_N_abs']} > {float(self.load_cell.limits[1])}", flush=True)
            self.emit_alarm(f"Load cell over HIGH limit: {self.data['load_N_abs']} > {float(self.load_cell.limits[1])}")
            load_check = True
        
        if self.data["load_N_abs"] < float(self.load_cell.limits[0]):
            print(f"alarm:load_cell:Load cell over LOW limit: {self.data['load_N_abs']} < {float(self.load_cell.limits[0])}", flush=True)
            self.emit_alarm(f"Load cell over LOW limit: {self.data['load_N_abs']} < {float(self.load_cell.limits[1])}")
            load_check = True
        
        if self.data["displacement_abs"] > float(self.extensometer.limits[1]):
            print(f"alarm:digital_extensometer:Extensometer over HIGH limit: {self.data['displacement_abs']} > {float(self.extensometer.limits[1])}", flush=True)
            self.emit_alarm(f"Extensometer over HIGH limit: {self.data['displacement_abs']} > {float(self.extensometer.limits[1])}")
            disp_check = True
        
        if self.data["displacement_abs"] < float(self.extensometer.limits[0]):
            print(f"alarm:digital_extensometer:Extensometer over LOW limit: {self.data['displacement_abs']} < {float(self.extensometer.limits[0])}", flush=True)
            self.emit_alarm(f"Extensometer over LOW limit: {self.data['displacement_abs']} < {float(self.extensometer.limits[1])}")
            disp_check = True
        
        # Motor check position end-stops and current limits
        
        
        if (load_check or disp_check or motor_check):
            print("Safety check failed IN FUNCTION")
            self.disable()
        
        # Return True only if all check pass
        return self.is_enabled()
    
    
    
    
    
    
    def halt(self):
        """ Halts all subsystems """
        #print("alarm:Controller halt called")
        self.motor.halt()
        self.disable()
        #self.stop_test()
        self.emit_alarm("System halted")
        #time.sleep(0.1)
        self.emit_status()
        
        return self
        
        



    def init_test(self, config):
        """
            This CANNOT work whilst a test is running 
        """

        self.test = BasicTest(config) # Load the BasicTest class with the relevant test configuration



        return self







    def get_values(self):

        """
            Get the current values of the UTM system
        """
        #print(self.data)
        return self.data
    
    
    
    def read_command(self, cmd):
        
        cmd = cmd.split(":")
        if cmd[0] == "speed":
            self.set_actuator_speed(float(cmd[1]))
            print(f"CMD to write to Arduino: {cmd}", flush=True)
        elif cmd[0] == "dir":
            self.set_actuator_direction(int(cmd[1]))
            print(f"CMD to write to Arduino: {cmd}", flush=True)
        elif cmd[0] == "led":
            self.set_led_brightness(int(cmd[1]), float(cmd[2]))
            print(f"CMD to write to Arduino: {cmd}", flush=True)
        elif cmd[0] == "enable":
            self.motor.enable()
            print(f"Motor enabled", flush=True)
        elif cmd[0] == "disable":
            self.motor.disable()
            print(f"Motor disabled", flush=True)
        
        else:
            print("Sorry, command not recognised. Please try again...", flush=True)
        


if __name__ == "__main__":
    
    con = Controller().init()
   
    ## Uncomment this block to be able to send cli inputs to the controller
    ## Comment this entire block when using it solely with the Electron GUI application
    while True:
        cmd = input("Enter controller command and press Return:\n")
        if cmd:
            try:
                con.read_command(cmd)
                
                time.sleep(0.01)
                con.motor.readI2C()
                
            except BaseException as err:
                print(err)



