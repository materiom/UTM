const { remote } = require('electron')

const path = require('path')
const {spawn} = require('child_process')
const moment = require("moment")
const axios = require("axios") 
const uuid = require("uuid")
var zmq = require("zeromq/v5-compat"); // Use if ZeroMQ version == 6 .Socket messaging library to talk to the Python scripts running in the background
//var zmq = require("zeromq"); // Use if ZeroMQ version == 5. Socket messaging library to talk to the Python scripts running in the background

const Log = require("../modules/logger.js").Logger
var logger = new Log()
const Config = require("../modules/configuration.js").Config
var Datastore = require('nedb-promises')

 
var vueApp = new Vue({
    el: '#app',
    data: {
        debug_mode: false, // Sets certain options to appear and the live charts to plot data at ALL times, not just during a test
        config: new Config(),
        testTypes: ["Tensile", "Compression"],
        dispZeroOffset: 0.0,
        loadZeroOffset: 0.0,
        test_db: Datastore.create({filename: './data/tests.db', autoload: true, timestampData: true }),
        values : { // Live values
            displacement_abs: 0.0,
            displacement_rel: 0.0,
            displacement_offset: 0.0,
            speed: 0.0,
            load_bit_abs: 0.0,
            load_bit_rel: 0.0,
            load_g_abs:0.0,
            load_g_rel: 0.0,
            load_N_abs: 0.0,
            load_N_rel:0.0,
            load_kN_abs: 0.0,
            load_kN_rel:0.0,
            stress_eng: 0.0,
            strain_eng: 0.0,
            stress_true: 0.0,
            strain_true: 0.0,
            motor_current:0.0,
            motor_setpoint: 0.0,
            motor_speed: 0.0,
            motor_direction: 0,
            motor_jog: 0,
            led1_brightness: 0,
            led2_brightness: 0,
            enabled: 0,
            ismoving: 1,
            
            active_section: {
                name: "",
                direction:0,
                setpoint: -1,
                control: -1,
                end: -1,
                endpoint: -1,
                input: false,
                delay: 0
            }
        },
        status:{
            test_ready: false,
            enabled: false,
            actuator_active: false,
            actuator_moving: false,
            actuator_direction: 1, // 1 = upwards (Tensile), -1 = down (Compression)
            led1: false,
            led2: false,
            estop: false,
            load_cell: false,
            test_running: false,
            test_paused: false,
            test_id: "",
            test_status: "Idle",
            digital_extensometer: false, 
            controller: false,
            jog_mode: "slow", // flag to state which jog speed will be used
            video_extensometer: false // Might not be active as it will be a optional extra for the UTM
        },
        test: {
            method: {},
            _id: undefined,
            data:[],
            time_elapsed: 0,
            date: undefined,
            start_time: undefined,
            preload: 0.0,
            max_load: 0.0,
            max_strain: 0.0,
            max_stress: 0.0,
            max_displacement: 0.0,
            sample: {
                id: "",
                type:  "", // tensile or compression
                material: {
                    id:"",
                    name :""
                }, // Name or ID? Do we need info on the specific formulation method too?
                gauge: {
                    len: 0.0,
                    thickness: 0.0,
                    width:0.0,
                    diameter: 0.0,
                    cross_section_area:0.0
                }
            }
        },
        sockets: {
            pub: zmq.socket("pub"), // ZMQ publishing socket for communication TO Controller python script
            sub: zmq.socket("sub"), // ZMQ subscription socket for reading communication FROM Controller python script
            padd: 'ipc://pub.ipc', // IPC socket name
            sadd: 'ipc://sub.ipc', // IPC socket name
            cam: zmq.socket("sub"),
            camadd : "ipc://camera.ipc"
        },
        materials:[],
        materials_db: {
            use: false,
            location: ""
        },
        load_units: "N",
        position_target: 0.0,
        controller_process: undefined, // spawned Python process that is running the Controller script
        tests:[], // hold an array of existing tests
        events:[], // For logging
        alarms: [], // For alarm events (log.type == alarm)
        camera_src:"" // For storing base64 strings to show the camera stream
    },
    mounted: function(){
        //this.test_db.loadDatabase()
        this.tests = this.test_db.find({}) // Load Test results
        this.init()
        
        console.log(this.config.config)
    },
    computed: {
        check_test: function(){
            console.log("Checking test validity")
            if(
                this.test.id
            ){
                //logger.log("Test information ready", "success")
                return true
            }
            else{
                //logger.log("Not all test information has been filled in", "warning")
                return false
            }

        },
        check_method: function(){
            if(this.test.method){
                if(
                     this.test.method.id
                    && this.test.method.type
                    && this.test.method.control_type
                    && this.test.method.stop_type
                    && this.test.method.control_point
                    && this.test.method.stop_point

                ){
                    //logger.log("Test information ready", "success")
                    return true
                }
                else{
                    //logger.log("Not all test information has been filled in", "warning")
                    return false
                }
            }
            else{
                //logger.log("Not all test information has been filled in", "warning")
                return false
            }

        },
        check_sample: function(){
            
            if(
                this.test.sample.id
                && this.test.sample.material.name
                && this.test.sample.gauge.len
                && this.test.sample.gauge.cross_section_area

            ){
                 
                if(this.test.sample.gauge.cross_section_area > 0.0){
                    return true
                }
                else{
                    return false
                }

            }
            else{
                return false
            }
        },
        check_subsystems: function(){
              
             
            if(
                this.check_controller
                && this.check_sample
                //&& this.check_test // Removed for now
                && this.check_method
            ){
                this.status.test_ready = true
                
                return true

            }
            else {
                this.status.test_ready = false
                return false
            }

        },
        check_controller: function(){
           return this.status.controller
        }

    },
    methods: {
        calc_csa: function(){

            this.test.sample.gauge.cross_section_area = 0.0
            
            if(this.test.sample.type == "rectangular"){
                this.test.sample.gauge.cross_section_area =  Number(this.test.sample.gauge.width * this.test.sample.gauge.thickness).toFixed(3)
            }
            else if(this.test.sample.type == "circular"){
                this.test.sample.gauge.cross_section_area =   Number( Math.PI * ((this.test.sample.gauge.diameter/2)**2) ).toFixed(3)
            }


        },
        moment: function(time, format){
            return moment(time).format(format)
        },

        duration: function(time, format){  
            return moment(moment.duration(time)).format(format)
        },

        init: async function(){
            var self = this

            

            self.init_communications()

            
            self.events = await logger.get_recent_events()
            
            self.alarms = await logger.get_alarms()
            
            console.log(self.events)
            logger.log("Initialising UTM")
            
            await self.config.load()
            
            // Check Emergency Stop status

            // Read a GPIO pin for this
            // also subscribe to any changes in the GPIO pin state


            // Start the Controller script
            // This may already be running in the background if I can get the blinkin'
            // zeromq or nanomsg sockets working on the Pi. In which case, don't start it, 
            // but do check communications with it are active and it's status is OK
            self.start_Controller()
           

        },





        init_communications: function(){
            //  initialise IPC comms between the GUI and the UTM Controller Python scripts
            var self = this
            
            
            self.sockets.pub.bind(self.sockets.padd);
            
            self.sockets.sub.connect(self.sockets.sadd);
            self.sockets.sub.subscribe("");
            
            
            self.sockets.cam.connect(self.sockets.camadd);
            self.sockets.cam.subscribe("");

            
            self.sockets.cam.on('message', function (msg) {
                //console.log(msg)
                var pic = msg.toString("base64")
                var src = "data:image/jpeg;base64," + pic
                self.camera_src = src 
                
            })
                
                
                
            self.sockets.sub.on('message', function (msg) {
                try{
                    msg = JSON.parse(msg.toString('utf8'))
                    
                    //console.log(msg)
                    
                    if(msg.type == "data"){
                        self.values = msg.data
                        
                        /*
                        Object.keys(msg.data).forEach(d=> {
                            if(!d.startsWith("led")){
                                self.values[d] = msg.data[d]
                            }
                        })
                        */
                        
                        if(self.debug_mode || self.status.test_running){
                            self.test.data.push(self.values)
                            if(self.test.data.length > 2000){
                                self.test.data.slice(0,1)
                            }
                        }
                        
                    }
                    
                    else if(msg.type == "alarm"){
                        console.log(msg);
                        logger.log(msg.message, "alarm")
                    }
                    else if(msg.type == "status"){
                        //console.log(msg);
                        Object.keys(msg.message).forEach(d=> {
                            self.status[d] = msg.message[d]
                        })
                    }
                    else if(msg.type == "event"){
                        console.log(msg);
                        self.event = msg
                        
                        logger.log(`${msg.system} - ${msg.message}`,"info")
                        
                        if(msg.system == "test"){
                            
                            if(msg.message == "finished"){
                                self.openTestModal("Finished")
                            }
                            else if(msg.message == "start"){
                                logger.log("Test started","info")
                                // Now remove all previous plotted data from the live charts
                                self.$refs.plot_loaddisp.pData = []
                                self.$refs.plot_stressstrain.pData = []
                            }
                            else if(msg.message == "pause"){
                                logger.log("Test paused","info")
                            }
                            else if(msg.message == "resume"){
                                logger.log("Test resumed","info")
                            }
                            else if(msg.message == "stop"){
                                logger.log("Test stopped","info")
                                self.$refs.results.getTests() // Get all new tests in the results subcomponent
                            }
                        }
                    }
                }
                catch(err){
                    console.log(err)
                }
                     


            });






        },
        openTestModal: function(status){
                UIkit.modal.confirm(`<h2>Test has finished</h2><h3>${status}</h3>`)
                    .then(function() {
                        console.log('Confirmed.')
                    }, function () {
                        console.log('Rejected.')
                    });
        },
        sendToController:function(msg){
            /*
            * Send a string formatted message to the Controller
            * This is primarily used for debugging and testing Controller
            * functionality rather than as a main level of communications
            */
            console.log(`MSG sending from GUI: ${msg}`)
            this.sockets.pub.send(msg)
            
            
        },
       
        load_method: function(method){
            // Load a test method from the library into the GUI
            var self = this
            this.test.method = method
            logger.log(`Loaded method ${self.test.method.id}`, "success")
        },
       

        zero_load: function(){
            // Send a command to the controller to set the load_offset value
            // A response will be sent back to the 'sub' socket and can then be set
            // in the GUI
            this.sendToController("cmd:zero:load_cell")
        },
       
        zero_disp: function(){
            // Send a command to the controller to set the displacement_offset value
            // A response will be sent back to the 'sub' socket and can then be set
            // in the GUI
            this.sendToController("cmd:zero:digital_extensometer")
        },
        enable_motor: function(){
            this.sendToController("cmd:enable")
        },
        disable_motor: function(){
            this.sendToController("cmd:disable")
        },
        jog_apart: function(){
            this.sendToController("cmd:jog:2")
        },
        jog_together: function(){
            this.sendToController("cmd:jog:1")
        },
        jog_stop: function(){
            this.sendToController("cmd:dir:0")
        },
        jog_mode_toggle: function(){
            // Toggle the max speed at which we can jog the UTM position
            var jog_mode = this.status.jog_mode == "slow" ? "fast" : "slow"
            this.sendToController(`mode:jog:${jog_mode}`)
        },
        move_to_position: function(position, speed){
            var self = this
            if(!position){
                var position = this.position_target
            }
            if(!speed){
                var speed = 30 // 0-100% 30 = slowest sensible speed that wont stall the motor 
            }

            // Now initiate move by communicating to the controller process script

            this.sendToController(`cmd:motor:position:${position}`) // command : send to motor module : define position : position in millimetres

        },
        
        setLED: function(num, val){
            
            if(num){
                this.values["led"+ num +"_brightness"] = val
                this.sendToController(`cmd:led:${num}:${val}`)
            }
            
            
            
        },
        setMotorSpeed: function(num){
            this.sendToController(`cmd:speed:${num}`)
        },
        
        start_test: function(){
            var self = this
            // Initialise status flags
            try {
                // Check user inputs so that we have enough information to work with
                if(
                        this.check_method
                        //&& this.check_test
                        && this.check_sample
                ){

                    // Make sure folders exist to save the data in - or will this be done with the Python control.py script?
                    self.test.start_time = moment().format("hh:mm:ss")
                    self.test.date = moment().format("DD/MM/YYYY")
                   
                    

                    // Make checks for each of the modules via the Controller
                    if(self.check_subsystems){
                        
                        // Force these two status items to be true to flag to the GUI that the test has started
                        // The Controller has ultimate control over these statuses but will have a short reliable delay
                        // to allow the user to manually press [STOP TEST] if required
                        //self.status.test_running = true
                        //self.status.test_paused = true
                        
                        
                        
                        // Zero out the live data to reset the charts
                        self.test.data = []
                        
                        var test_id = uuid.v4() // UUID for the test data so that it can be tracked through the test workflow
                        
                        self.test._id = test_id // Add this id to the TEST object to help identify the test data CSV file afterwards
                        
                        
                        
                        
                        // Save metadata for the test in a database - use nedb for ease?
                        
                        
                        
                        
                        fs.appendFileSync(`./data/tests.db`, JSON.stringify(self.test) + "\n")
                        
                        
                        // Save metadata in a file
                        fs.writeFileSync(`./data/${test_id}.json`, JSON.stringify(self.test))
                        
                        
                        
                        
                        
                        
                        
                        // Signal controller to start test
                        this.sendToController(`test:start:${test_id}`) // command : doing a test metod : start test : test_id in the database

                        

                        logger.log("Started. Waiting for controller to initiate test.","info")
                        
                    }
                    else {
                        throw new Error("Controller is not ready.<br>Test aborted")

                    }
                    
                }
                else {
                    throw new Error("Pre-test information checks failed.<br>Test cannot be run.")
                }


            }
            catch(err){
                // One of our checks above has failed
                logger.log(err.message, "alarm")

                self.status.test_running = false
                self.status.test_paused = false
            }



        },
        pause_test: function(){
            var self = this
            this.sendToController(`test:pause`) // command : doing a test metod : stop
            logger.log("Pausing test","info")

        },
        resume_test: function(){
            var self = this
            this.sendToController(`test:resume`) // command : doing a test metod : stop
            logger.log("Resuming test","info")

        },
        stop_test: function(){
            var self = this
            this.sendToController(`test:stop`) // command : doing a test method : stop

            logger.log("Stopping test","info")
            self.$refs.results.getTests() // Get all new tests in the results subcomponent

        },
        emergency_stop: function(){
            var self = this
            this.sendToController(`test:stop`) // command : doing a test metod : stop
            logger.log("Emergency Stop","alarm")
        },
        init_Controller: function(){
            if(self.controller_process.connected){
                self.controller_process.close()
            }
            self.start_Controller()
            
        },
        change_load_units: function(){
            /**
             * Iterate through a change of load cell units for the UI displays
             * 
             * 
             * */
            if(this.load_units == "bits"){
                    this.load_units = "g"
            }
            else if(this.load_units == "g"){
                    this.load_units = "N"
            }
            else if(this.load_units == "N"){
                    this.load_units = "kN"
            }
            else if(this.load_units == "kN"){
                    this.load_units = "bits"
            }
            
        },

        start_Controller: function(){
            var self = this

            // load controller config in here?
            
            let script = self.config.config.controller.script
           
            self.controller_process = spawn('python3', ["-u", script, JSON.stringify(self.config.config.controller)]);

            self.controller_process.on('spawn', function () {
                //console.log("\x1b[35m","[UTM-Controller] => Process started","\x1b[0m" );
                logger.log("[UTM-Controller] => Process started")
                //self.status.controller = true // controller should send its own status signal when it has started successfully
            });

            self.controller_process.stdout.on('data', function (data) {
                console.log("\x1b[35m" , `[UTM-Controller] => ${data.toString()}`,"\x1b[0m" );
            });

            self.controller_process.stderr.on('data', function (data) {
                console.log("\x1b[31m",'[UTM-Controller] => Python Error from script: ', data.toString(),"\x1b[0m");
                logger.log("[UTM-Controller] => Error from controller")
            });

            self.controller_process.on('close', (code) => {
                //console.log(`[UTM-Controller] => Process close all stdio with code ${code} => `);
                logger.log("[UTM-Controller] => Service closed")
            });

            self.controller_process.on('exit', (code, signal) => {
                console.log("[UTM-Controller] => Exited");
                logger.log("[UTM-Controller] => Service exited")
                self.status.controller = false
            });
        }


    
    
    }
})























