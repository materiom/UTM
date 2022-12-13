import json
import time # for delay functions

class BasicTest:
    def __init__(self, controller, logger=None, test=None):
        self.controller = controller
        self.is_paused = False
        self.is_running = False # Flag to show if the test is current active and running
        self.is_moving = False
        
        self.status = "idle"
        self._id = None # defines the test ID in the database
        
        self.data = None # Store the current data values from the test controller
        self.sections = []
        self.initial_data = {}
        
        self.current_direction = 0
        
        
        self.max_load = 0.0 # Absolute value of peak load during a test

        self.active_section = 0 # Start with the first section
        self.test = None
        self.method = None

        self.sample = None
        
        if not test is None:
            self.test = test
            self.method = test["method"]
            self.sample = test["sample"]


        if not logger is None:
            self.logger = logger
          
        
        
        self.delay = {  "start": -1, "current": -1 }
    
    
    def init(self, test=None):
        """
            Initialise a new test if there isn't already one running
            test is as dict() containing all the information required to
            define the required mechanical test
        """
        
        self.sections = []
        self.test = test
        self.method = test["method"]
        self.sample = test["sample"]
        
        # Generate the test method
        self.generate()

        # Initialise the data logger with the correct test ID 
        self.logger.init(test_id=self.test["_id"])
        
        
        
        self.max_load = 0.0 # Absolute value of peak load during a test


        return self
    
    
    def go_to_position(self, val:float):
        
        """
            Make the machine go to the specified position
            Uses this class to do it but doesn't log the data
        """
    
    
    
    
    def generate(self):
        """
            Generate the test protocol from the provided method
        """
        try:
            if not self.method is None:
                # Method exists so lets generate some sections for the tests
                
                # Set the direction of motor travel for each section based on the test type
                
                
                self.reset()
                
                
                
                if self.method["type"] == "compression":
                    direction = 1
                elif self.method["type"] == "tensile":
                    direction = 2
                    
                    
                # Test preload section - the first section to run if it is defined
                if "preload" in self.method:
                    if float(self.method["preload"]) > 0.0: # Check that the required preload is non-zero
                        section = {
                            "name": "Preload", # Preload section
                            "direction": direction, # Direction of travel for the preload
                            "setpoint": float(self.method["preload"]),  # Preload value to hold the sample at before testing
                            "control": "load", # Use relative load for this control 
                            "end":"load",
                            "endpoint": float(self.method["preload"]),
                            "input": False,# Wait for user input to continue to the next section of the test.
                            "delay": 10 # Wait for 10 seconds until we move to the next section. This works in conjunction with "end" and "input".
                         }
                        
                        self.sections.append(section)
               
                ##
                ## Future improvement - multistage testing
                ## 
                ## Make an array within the test.method
                ## For each element in the array we can define a new test section
                ## Iterate through each element to create a new section in the test
               
                # Main test section
                section = {
                    "name": "Section 1", # If this is multistage test, iterate the section number too
                    "direction": direction, # It might be possible to do fatigue/cyclic tests in the future so this direction might be irrelevant at that stage
                    "control": self.method["control_type"],
                    "setpoint": float(self.method["control_point"]),
                    "end": self.method["stop_type"],
                    "endpoint": float(self.method["stop_point"]),
                    "input": False,
                    "delay": 0
                 }
                
                self.sections.append(section)
                 
                #print("Sections", flush=True)
                print(self.sections, flush=True)
                
                
            else:
                print("Cannot generate test procedure. Method not defined", flush=True)
                
        except BaseException as err:
            print(err, flush=True)
        
        return self
    
    
    
    
    
    
    
    def check_progress(self, userinput=None):
        """
            Check whether the data has passed control endpoints and if so go to the next section
            IF section["endpoint"] == 'wait_for_input' then the function
            Uses the input kwarg to feed user input to the function to manually switch sections 
        """  
        
        
        ## Update any MAX values
        
        if abs(self.data["load_N_rel"]) > abs(self.max_load): ## Uses a minimum viable max load to ensure noise doesn't stop the test prematurely
            self.max_load = abs(self.data["load_N_rel"])
            #print(f"Max Load: {self.max_load}", flush=True)
        
        ## Check what we will be checking live data against
        
        user_input = self.sections[self.active_section]["input"] # Are we waiting for user input?
        delay = self.sections[self.active_section]["delay"] # Do we want a delay at the end of the segment once the limit has been reached
        end = self.sections[self.active_section]["end"] # End type to check
        
        reason = ""
        
        if end == "displacement":
            end_key = "displacement_rel"
        elif end == "strain":
            end_key = "strain_eng"
        elif end == "load":
            end_key = "load_N_rel"
        
        endpoint = self.sections[self.active_section]["endpoint"] # End value to check against
        self.current_direction = self.sections[self.active_section]["direction"] # Direction of motor travel to check values against

        ready = False # Flag to check if the section endpoint has been reached and whether we shift to user_input or delay mode

        # Setting a delay will supersceed any user_input requirements

        #print(ready, flush=True)
        if end == "displacement" or end == "strain" or end == "load":
            if self.current_direction == 2:
                check = self.data[end_key] > endpoint
                
                if check == True:
                    if end == "load":
                        self.current_direction = 0
                        reason = "Load control tripped"
                    print(f"Tripped in direction > 0", flush=True)
                    
                    reason = "Displacement tripped"
                    
                    ready = True # go to next section if True
            elif self.current_direction == 1:
                check = abs(self.data[end_key]) > endpoint
                if check == True:
                    if end == "load":
                        self.current_direction = 0
                        reason = "Load control tripped"
                    print(f"Tripped in direction < 0", flush=True)
                    reason = "Displacement tripped"
                    ready = True # go to next section if True





        ## End point check for sample failure - load dropped to 10% of peak load
        if end == "failure" and abs(self.max_load) > 10:
            if abs(self.data["load_N_rel"]) / abs(self.max_load) < 0.1: # Current load has dropped to 10% of peak load
                ready = True # go to next section if True
                reason = "Load failure tripped"
          





        if ready == True:
            print("Endpoint has been reached. Making further checks", flush=True)
            if user_input == False and delay > 0: # We are ONLY waiting for the delay to end before moving onto the next section
                if self.delay["start"] < 0: # delay hasn't yet started so we will activate it
                    self.delay["start"] = time.time()
                else: # Delay start > 0 therefore it has started so we will check whether we have exceeded the delay limit before shifting to the next section
                    # Now wwe are counting and checking whether we have waited long enough - THIS MIGHT BE BETTER IN A SEPARATE THREAD?!
                    self.delay["current"] = time.time()
                    if self.delay["current"] - self.delay["start"] >= delay:
                        # We have now exceeded the delay so go to next()
                        print("Delay time exceeded. Moving to next step", flush=True)
                        self.delay = {  "start": -1, "current": -1 } # Reinitialise the delay for the next section if required
                        self.next(reason) # go to next section
            

            elif user_input == True and delay == 0:
                # We will wait for user input to shift to next section. No delay detected
                if not userinput is None: # If we detect user input go to next() 
                    self.next(reason)

            elif user_input == False and delay == 0:
                # No delay or user_input requested by this section so go straight to next()
                self.next(reason) # Go to next section
         
           


        return self



    def reset(self):
        """
            Reset the test and test method so that is doesn't overwrite any existing data
            This is normally used at the start of a new test so that it ensures a NEW test
            can be started.
            Don't use this at the END of a test as the test may need to remain in memory for
            subsequent saving or analysis etc.
        """
        print("Resetting BasicTest ready for a new test", flush=True)
        self.initial_data = {}
        self.sections = []
        self.max_load = 0.0



    def next(self, message=None):

        """
            Move to the next phase of the test
        """
        self.active_section += 1
        print("Moving to next test section...", flush=True)
        if self.active_section >= len(self.sections): # Do we still have sections left to use?
            print("No more sections to test. Test has finished!", flush=True)
            if not message is None:
                self.stop(message)
            else:
                self.stop()
        return self



    def get_setpoints(self):
        """
            Return the relevant setpoints to the controller to tell it how to control the test
        
        """
        #print("Section",self.active_section, flush=True)
        section = self.sections[self.active_section]
        if section["control"] == "speed":
            return { "type": "speed", "speed": section["setpoint"], "direction": self.current_direction }
        
        if section["control"] == "strainrate":
            return {  "type": "strainrate", "strainrate": section["setpoint"], "direction": self.current_direction }

        if section["control"] == "load":
            return {  "type": "load", "load": section["setpoint"], "direction": self.current_direction }



    def start(self):
        """
           Run the test method that is currently loaded 
        """
        if not self.is_running:
            print("STARTING TEST in BasicTest class", flush=True)
            # Check if a valid test method is loaded in this Class
            
            # If method is loaded and ready to run
            if len(self.sections) > 0:
                # Set running flag
                self.is_paused = False
                self.is_running = True
                self.status = "inprogress"    
                self.active_section = 0
                self.logger.start()
                
                return True
                
                
            else:
                return False



            
    def stop(self, message=None):
        """
           STOP the test and tidy things up 
        """
        if self.is_running == True:
            print("STOPPING TEST in BasicTest class", flush=True)
            # Set running flag
            self.is_paused = False
            self.is_running = False
            self.status = "finished"
            
            self.logger.stop() # Stop data logging
            self.cleanup() # this also combines the json metadata and csv files together
            
            # Stop the controller too
            if not message is None:
                self.controller.finish_test(message)
            else:
                self.controller.finish_test()



    def pause(self):
        """
           PAUSE the current test 
        """
        print("PAUSING TEST in BasicTest class", flush=True)
        # Set running flag
        self.is_paused = True
        self.is_running = False
        self.status = "paused"



    
    def resume(self):
        """
           RESUME the current test 
        """
        print("RESUMING TEST in BasicTest class", flush=True)
        # Set running flag
        self.is_paused = False
        self.is_running = True
        self.status = "inprogress"
    


   

    def cleanup(self):
        meta_file = open(f"./data/{self.test['_id']}.json","r")
        meta = json.load(meta_file)
        
        test_datafile = open( f"./data/{self.test['_id']}.csv", "r")
        testdata = str(test_datafile.read())
        
        
        newfile = open( f"./data/{self.test['_id']}_finished.csv", "w"  )
        
        
        newfile.write( "# Materiom UTM Datafile\n" )
        newfile.write( f"#\n" )
        newfile.write( f"#\n" )
        newfile.write( f"# TEST ID,{self.test['_id']}\n" )
        newfile.write( f"#\n" )
        newfile.write( f"#\n" )
        newfile.write( f"# SAMPLE ID,{self.sample['id']}\n" )
        
        newfile.write( f"# MATERIAL,{self.sample['id']}\n" )
        
        newfile.write( f"# SAMPLE TYPE,{self.sample['type']}\n" )

        newfile.write( f"# SAMPLE GAUGE LENGTH,{self.sample['gauge']['len']}\n" )
        if self.sample['type'] == "circular":
            newfile.write( f"# SAMPLE GAUGE DIAMETER,{self.sample['gauge']['diameter']}\n" )
            
        if self.sample['type'] == "rectangular":
            newfile.write( f"# SAMPLE GAUGE WIDTH,{self.sample['gauge']['width']}\n" )
            newfile.write( f"# SAMPLE GAUGE THICKNESS,{self.sample['gauge']['thickness']}\n" )
            
        newfile.write( f"# SAMPLE GAUGE CSA,{self.sample['gauge']['cross_section_area']}\n" )
        newfile.write( f"#\n" )
        newfile.write( f"#\n" )
        newfile.write( f"# METHOD NAME,{self.method['id']}\n" )
        newfile.write( f"#\n" )
        for s in self.sections:
            newfile.write( f"# SECTION NAME,{s['name']}\n" )
            newfile.write( f"# DIRECTION,{s['direction']}\n" )
            newfile.write( f"# CONTROL TYPE,{s['control']}\n" )
            newfile.write( f"# SETPOINT ,{s['setpoint']}\n" )
            newfile.write( f"# END TYPE,{s['end']}\n" )
            newfile.write( f"# ENDPOINT,{s['endpoint']}\n" )
            newfile.write( f"# INPUT,{s['input']}\n" )
            newfile.write( f"# DELAY,{s['delay']}\n" )
            
            newfile.write( f"#\n" )
        
        newfile.write( f"#\n" )
        newfile.write( f"#\n" )
        
        
        # Now write the test data
        newfile.write( testdata )
        
        # Close all the files
        newfile.close()
        meta_file.close()
        test_datafile.close()
