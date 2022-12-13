// logger.js

// Used to log events from the Controller


'use strict';

const fs = require("nedb")
var Datastore = require('nedb-promises')
var moment = require('moment')


module.exports.Logger = class Logger {
    constructor() {
        this.type = 'default'; // default or user
        this.config = {}
        this.db = undefined
        this.init()
    }
    
    init(){
        var self = this
        console.log("[Logging] => Loading Logs")
        try {
            self.db = Datastore.create({filename: './logs/logs.db', autoload: true, timestampData: true })
            self.get_recent_events(200)
        }
        catch(err) {
            console.error(err)
        }
    }

    log(msg, type){
        message(msg, type)
        this.db.insert({ts: moment().format("HH:mm:ss DD/MM/YY"), text: msg, type: type})
        this.get_recent_events(200)
    }

    async get_recent_events (num) {
        
        if(!num){var num = 200}

        return await this.db.find({})
                        .limit(num)
                        .sort({ts:-11})
                        .then(evts => {
                            return evts
                        })
    }

     async get_alarms (num) {
        
        if(!num){var num = 20}

        return await this.db.find({"type": "alarm"})
                        .limit(num)
                        .sort({ts:-11})
                        .then(evts => {
                            return evts
                        })
    }


}


function message(msg, type="info"){
    console.log(msg, type)
    if(type == "alarm"){  type == "danger" }
    else if(type == "info"){  type == "primary" }
    
    //Close all open messages before displaying a new one
    UIkit.notification.closeAll()
    // Display the new message
    UIkit.notification({
          message: msg,
          status: type,
          pos: 'bottom-right',
          timeout: 3000
      });

}


