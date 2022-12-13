# data_logger.py
import time
from datetime import datetime
from threading import Thread
import json

class Logger:
    def __init__(self, config=None, socket=None, debug=False):
        self.config = config
        self.log_frequency = int(self.config["frequency"]) # Logging rate in Hz (approx)
        self.isLogging = False
        self.debug = debug
        self.logFile = None
        self.test_id = None
        self.start_time = 0.0
        self.data = []
        
        self.write_thread = None
        
        if self.debug == True: # If the debug flag is set True then we will store ALL CSV data as we go along... not just for a test
            self.init()
            self.start()


    def init(self, test_id=None):
        """
             Creates a new logging file and writes metadata to it
            
        """
        try:
            if not test_id is None:
                self.test_id = test_id
                # If we have a test_id use it for the filename
                self.logFile = open(f"./data/{self.test_id}.csv", "w+")
                print("Initialised data logger for test: " + self.test_id, flush=True)
        except BaseException as err:
            print(err, flush=True)
        
        return self
    




    def start(self):
        """
            Start the data logger and write rows to it in a separate thread loop
        """
        if not self.logFile is None:
            self.start_time = time.time()
            self.write_headers()
            
            
            # Once headers have been written, allow the rows of data to be logged
            self.isLogging = True
            
            self.write_thread = Thread(target=self.write_loop, args=[])
            self.write_thread.daemon = True
            self.write_thread.start()
        else:
            #self.init()
            print("Logfile has not been opened properly. Cannot write to it", flush=True)
            
        return self




    def stop(self):
        """
            If the logFile exists, stop writing rows and close the file
        """
        self.isLogging = False
        self.test_id = None
        
        if not self.logFile is None:
             self.logFile.close()
            
            
        return self


    def write_headers(self):
        try:
            if not self.logFile is None:
                headers = "time,section,disp_abs,disp_rel,speed,load_N_abs,load_N_rel,strain_eng,strain_true,strain_rate,stress_eng,stress_true,motor_speed_setpoint,motor_speed,motor_current"
                self.logFile.write(f"{headers}\n")
                
                units = "s,1,mm,mm,mm/s,N,N,1,1,1/s,MPa,MPa,bits,pulses/min,A"
                self.logFile.write(f"{units}\n")
                
                self.logFile.flush()
        except BaseException as err:
            print(f"Cannot write headers to CSV data logging file for test: {self.test_id}", flush=True)
        return self
    
    
    
    def update(self, data=None):
        """
            Update the data from an external source
        """

        try:
            if not data is None:
                self.data = data
        except BaseException as err:
            pass

        return self
    
    
    
    def write_loop(self):
        """
            Continuously write a new row to the logFile at the correct frequency
        """
        
        while self.isLogging:
            self.write_row()
            time.sleep((1.0/self.log_frequency)-0.001)
              
    
    
    def write_row(self):
        """

        """
        try:
            
            if not self.logFile is None:
                self.data["time"] = time.time() - self.start_time # Convert times to start at close to 0.000s
                row = f"{self.data['time']:.3f},{str(self.data['active_section']['name'])},{self.data['displacement_abs']:.3f},{self.data['displacement_rel']:.3f},{self.data['speed']:.3f},{self.data['load_N_abs']:.3f},{self.data['load_N_rel']:.3f},{self.data['strain_eng']:.3f},{self.data['strain_true']:.3f},{self.data['strain_rate']:.3f},{self.data['stress_eng']:.3f},{self.data['stress_true']:.3f},{self.data['motor_setpoint']},{self.data['motor_speed']},{self.data['motor_current']}"
                row += "\n"
                self.logFile.write(row)
                self.logFile.flush()

        except BaseException as err:
            print(f"Cannot write row to CSV data logging file for test: {self.test_id}", flush=True)
            print(err)
                
        return self

        
