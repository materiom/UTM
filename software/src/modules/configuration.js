// configuration.js
'use strict';

const fs = require('fs')

var Datastore = require('nedb-promises')
var moment = require('moment')


const { SerialPort } = require('serialport')


module.exports.Config = class Configuration {
    constructor() {
        this.type = 'default'; // default or user
        this.config = {
            modules: {
                load_cell: {
                    emulated: false,
                    amplifier: "HX711",
                    gpio: {
                        data: 5,
                        clock: 6
                    },
                    script: "",
                    units: "kN",
                    limits:[-10.0,10.0],
                    calibration: {
                        gain: 1,
                        intercept: 0
                    }
                },
                digital_extensometer: {
                    emulated: false,
                    port: "",
                    baudrate: 115200,
                    script: "",
                    units: "mm",
                    limits:[0,300.0],
                    calibration: {
                        gain: 1,
                        intercept: 0
                    }
                },
                led1: {
                    limits:[0,100]
                },
                led2: {
                    limits:[0,100]
                }
            },
            controller: {
                emulated: false,
                port: "",
                baudrate: 115200,
                script: "",
                gpio: {
                        sda: 21,
                        scl: 23
                },
                pid: {
                        kp: 50,
                        ki: 2,
                        kd: 0.05
                },
                logging:{
                    frequency: 10
                }
            }
        }
        this.ports = []
        this.db = undefined


        this.init()
    }

    init(){
        var self = this
        console.log("[Configuration] => Initialising")
        try {

            // get a list of valid serial ports to connect to
            SerialPort.list().then(ports => {
                console.log(ports)
                self.ports = ports
            });


            //self.load()
        }
        catch(err) {
            console.error(err)
        }

        


    }

    async load() {
        var self = this
        console.log("[Configuration] => Loading db")
        try {
            if (fs.existsSync('./config/user.db')) {
                
                self.db = Datastore.create('./config/user.db');
                self.db.loadDatabase()
                await self.db.findOne({}).then(c => {
                    if(c != null){
                       self.config = c
                    }
                })

                self.type = "user" // using user defined configuration
                
                console.log("[Configuration] => Using user-defined configuration")
            }
            else {

                self.db = Datastore.create('./config/default.db');
                self.db.loadDatabase()
                
                await self.db.findOne({})
                    .then( c => {
                        if(c != null){
                            self.config = c
                        }
                        else{
                            throw Error("Cannot load default configuration. Using internal defaults")
                        }
                    })
                    .catch(err => {
                        self.save()
                    })
                
                console.log("[Configuration] => Using the default configuration")
            }


          } catch(err) {
            console.error(err)
          }
    }
    async reload() {
        // Reloads the existing database once it has been updated
        self.db.loadDatabase()
            await self.db.findOne({}).then(c => {
                if(c != null){
                   self.config = c
                }
            })
            

    }

    save() {
        var self = this
        try {
            self.db.update({_id:self.config._id}, self.config)
                .then(res => {
                    console.log("[Configuration Manager] => Saved updated user configuration as 'user.db'") 
                })

        } catch(err) {
            console.error(err)
        }


    }

    setConfig(conf){
        try {
            this.config = conf
            this.save()
        }
        catch(e){
            console.log(`[Configuration Manager] => Error when trying to set new configuration: \n${err.message}\n`)
        }
    }


    get() {
        if(Object.keys(this.config).length == 0){
            this.load()
        }
        return this.config
    }

    set( key, value ){
        try {
            this.config[key] = value
            this.save()
        }
        catch(e){
            console.log(`[Configuration Manager] => Error when trying to set a new value: \n${err.message}\n`)
        }

    }
    

}




