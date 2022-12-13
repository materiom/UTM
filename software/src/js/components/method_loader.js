var Datastore = require('nedb-promises')
const fs = require("fs")

Vue.component('method-loader', {
    props: ["status"],
    data: function(){
        return {
            db: Datastore.create({filename: './data/methods.db', autoload: true, timestampData: true }),
            selectedMethod:{},
            test_methods: [],
            sortKey: "id",
            sortDir: 1
    
        }
    },
    watched: {
       

    },
    mounted: function(){
        //this.db.loadDatabase()
        this.get_methods()

    },
    computed:{



    },
    methods: {
        sort: function(key){
            if(this.sortKey == key){
                this.sortDir = this.sortDir == 1 ? -1 : 1 // Toggle sort direction
            }
            else {
                this.sortKey = key // Change the db key to sort the results on
            }

            this.get_methods() // Now re-get all the methods from the database again

        },
        new_method: function(){
            this.selectedMethod = {  id: "" }
        },
        get_methods: function(){
            var self = this

            var dir = this.sortDir
            var skey = this.sortKey

            //console.log(skey, dir)
            
            this.db.find({}) // find ALL methods
                .sort({ skey : dir }) // Sort using this key and direction
                .then(methods => { // Now you've returned the found methods do something with them
                   
                    self.test_methods = methods
                })
        },
        delete_method: function(method){
            var self = this
            var answer = confirm("Are you sure you want to delete this method?")
            if(answer == true){
                this.db.remove({_id: method._id})
                .then(res => {
                    console.log("Deleted method")
                    self.get_methods()
                })
                .catch( err => {
                    console.log(err)
                })
            }
            

        },
        load_method: function(method){
            this.selectedMethod = method
            this.$emit("load", method)
            this.close_modal(500)
        },
        save_method: function(){
            var self = this
            //console.log(this.selectedMethod)
            delete this.selectedMethod._id // Remove this in case it is left over from loading from the library

            if (
                this.selectedMethod.id
                && this.selectedMethod.type
                && this.selectedMethod.control_type
                && this.selectedMethod.control_point
                && this.selectedMethod.stop_type
                && this.selectedMethod.stop_point

            ){
                 // Save the method in method.db

                 this.db.insert(self.selectedMethod)
                        .then(doc => {
                            console.log(doc) // Notify user that it has saved
                            self.get_methods()
                        }) 

            }
            else{
                logger.log("Cannot save this method. Not all information has been filled in", "warning")
                throw new Error("Not all test information has been filled in")
            }



        },
        onFileChange: async function(e){
            // Opens a file dialog and allows the user to open a json method file that was shared or export from another UTM user
                var self = this
                var files = e.target.files || e.dataTransfer.files;
                if (!files.length)
                    return;
                    var array = Array.from(files)


                    for(var i=0; i < array.length; i++){
                        if(i == array.length-1){

                            const myNotification = new Notification('Finished Import', {
                              body: `Imported ${files.length} files`
                            })
                        
                        }

                        await self.import_method_file(files[i])

                    }
                    self.get_methods()

        },
        import_method_file: async function(file){
            var self = this
            console.log(file)

            var method = JSON.parse(fs.readFileSync(file.path, 'utf8'));

            return this.db.insert(method)
                            .then(doc => {
                                console.log(doc) // Notify user that it has saved
                                self.get_methods()
                            }) 


        },
        open_modal: function () {
            var modal = this.$refs.modal
            var modal = UIkit.modal(modal)
            modal.show()
        },
        close_modal: function (delay) {
            var modal = this.$refs.modal
            var modal = UIkit.modal(modal)
            modal.hide(delay)
        }
        
    },
    template:`
    <div>
        <div class="uk-padding-small uk-width-1-1 uk-grid-small uk-flex uk-flex-between uk-child-width-1-3" uk-grid>
            

            <div v-if="'id' in selectedMethod">
                <div class="uk-link uk-hover uk-flex uk-flex-column uk-text-center" @click="new_method" uk-tooltip="Reset test method">
                    <i :class="[ 'id' in selectedMethod ? '':'fa-lg', 'fa', 'fa-refresh' ]"></i>
                    <span v-show="!('id' in selectedMethod)">New method</span>
                </div>
            </div>
            <div v-else>
                <div class="uk-link uk-hover uk-flex uk-flex-column uk-text-center" @click="new_method" uk-tooltip="New test method">
                    <i :class="[ 'id' in selectedMethod ? '':'fa-lg', 'fa', 'fa-plus-square-o' ]"></i>
                    <span v-show="!('id' in selectedMethod)">New method</span>
                </div>
            </div>


            <div>
                <div class="uk-link uk-hover uk-flex uk-flex-column uk-text-center" @click="open_modal" uk-tooltip="Open test method library">
                    <i class="fa fa-folder-open-o fa-lg"></i>
                    <span v-show="!('id' in selectedMethod)">Load from library</span>
                </div>
            </div>
            <div v-if=" 'id' in selectedMethod">
                <div class="uk-link uk-hover uk-flex uk-flex-column uk-text-center" @click="save_method" uk-tooltip="Save current test method">
                    <i class="fa fa-floppy-o fa-lg"></i>
                    <span v-show="!('id' in selectedMethod)">Save method</span>
                </div>
            </div>
        </div>

    <div v-if="'id' in selectedMethod">
        <table class="uk-table uk-table-small">
            <tbody>
                <tr>
                    <td>ID</td>
                    <td colspan=2>
                        <input class="uk-input" v-model="selectedMethod.id" type="text" :disabled="status.test_running || status.test_paused" @change="load_method(selectedMethod)"/>
                    </td>
                </tr>
               
                <tr>
                    <td>Type</td>
                    <td colspan=2>
                        <select class="uk-select" v-model="selectedMethod.type" :disabled="status.test_running || status.test_paused"  @change="load_method(selectedMethod)">
                            <option value="tensile">Tensile</option>
                            <option value="compression">Compression</option>
                        </select>
                    </td>
                </tr>
                 <tr>
                    <td>Preload</td>
                    <td>
                        <input class="uk-input" v-model="selectedMethod.preload" type="number" min=0.1 step=0.01 max=5 :disabled="status.test_running || status.test_paused" @change="load_method(selectedMethod)"/>
                    </td>
                    <td>kN</td>
                </tr>
                <tr>
                    <td>Control</td>
                    <td colspan=2>
                        <select class="uk-select" v-model="selectedMethod.control_type" :disabled="status.test_running || status.test_paused" @change="load_method(selectedMethod)">
                            <option value="speed">Speed</option>
                            <option value="strainrate">Strain Rate</option>
                        </select>
                    </td>
                </tr>
                <tr>
                    <td>Set point</td>
                    <td>
                        <input class="uk-input" v-model="selectedMethod.control_point" type="number" min=0 step=0.001 :disabled="status.test_running || status.test_paused" @change="load_method(selectedMethod)">
                    </td>
                    <td>
                        <span v-if="selectedMethod.control_type == 'speed'">mm/s</span>
                        <span v-if="selectedMethod.control_type == 'strainrate'"> 1/s</span>
                       
                    </td>
                </tr>
                <tr>
                    <td>Stop Type</td>
                    <td colspan=2>
                        <select class="uk-select" v-model="selectedMethod.stop_type" :disabled="status.test_running || status.test_paused" @change="load_method(selectedMethod)">
                            <option value="failure">Failure</option>
                            <option value="displacement">Displacement</option>
                            <option value="strain">Strain</option>
                            <option value="load" disabled>Load</option>
                            <option value="stress" disabled>Stress</option>
                            
                        </select>
                    </td>
                </tr>
                <tr>
                    <td>Stop Condition</td>
                    <td>
                        <input class="uk-input" v-model="selectedMethod.stop_point" type="number" min=0 step=0.001 :disabled="status.test_running || status.test_paused" @change="load_method(selectedMethod)">
                    </td>
                    <td>
                        <span v-if="selectedMethod.stop_type == 'displacement'">mm</span>
                        <span v-if="selectedMethod.stop_type == 'load'">kN</span>
                        <span v-if="selectedMethod.stop_type == 'strain'">1</span>
                        <span v-if="selectedMethod.stop_type == 'stress'">MPa</span>
                         <span v-if="selectedMethod.stop_type == 'failure'">% Max Load</span>
                    </td>
                </tr>
                <tr>
                    <td>Delay at end</td>
                    <td>
                        <input class="uk-input" v-model="selectedMethod.delay" type="number" min=0 step=0.1 :disabled="status.test_running || status.test_paused" @change="load_method(selectedMethod)">
                    </td>
                    <td> s</td>
                </tr>
            </tbody>
        </table>    
    </div>



    <div ref="modal" class="uk-modal-container"  uk-modal>
        <div class="uk-modal-dialog uk-modal-body" style="height: 80vh; overflow-y: scroll">

             <a class="uk-modal-close-default" type="button" uk-close @click="close_modal"></a>
                <h2 class="uk-text-center">Test Method Library</h2>


                <div class="uk-width-1-1 uk-padding-small">
                    <div uk-grid>
                        <div>
                             <button class="uk-button uk-button-primary" @click="$refs.file.click()" uk-tooltip="delay: 250; title:Import method file(s) to the library">
                                <i class="fa fa-upload"></i> Import
                             </button>
                        </div>

                        <input type="file" style="display:none" @change="onFileChange" ref="file" multiple />

                    </div>
                </div>

                <div class="uk-grid-small" uk-grid>
                    <table class="uk-table uk-table-small uk-table-divider uk-table-hover">
                        <thead>
                            <tr>
                                <th><b>LOAD</b></th>
                                <th>
                                    <div class="uk-link uk-hover" @click="sort('id')">
                                        ID  <i v-if="sortKey == 'id' " :class="[  sortDir == 1 ? 'fa-arrow-up' : 'fa-arrow-down', 'fa' ]"></i>
                                    </div>
                                </th>
                                <th>
                                    <div class="uk-link uk-hover" @click="sort('type')">
                                        Type  <i v-if="sortKey == 'type' " :class="[  sortDir == 1 ? 'fa-arrow-up' : 'fa-arrow-down', 'fa' ]"></i>
                                    </div>
                                </th>
                                <th>
                                    <div class="uk-link uk-hover" @click="sort('control_type')">
                                        Control Type  <i v-if="sortKey == 'control_type' " :class="[  sortDir == 1 ? 'fa-arrow-up' : 'fa-arrow-down', 'fa' ]"></i>
                                    </div>
                                </th>
                                <th>
                                    <div class="uk-link uk-hover" @click="sort('control_point')">
                                        Set Point  <i v-if="sortKey == 'control_point' " :class="[  sortDir == 1 ? 'fa-arrow-up' : 'fa-arrow-down', 'fa' ]"></i>
                                    </div>
                                </th>
                                <th>
                                    <div class="uk-link uk-hover"  @click="sort('stop_type')">
                                        Stop Type  <i v-if="sortKey == 'stop_type' " :class="[  sortDir == 1 ? 'fa-arrow-up' : 'fa-arrow-down', 'fa' ]"></i>
                                    </div>
                                </th>
                                <th>
                                    <div class="uk-link uk-hover" @click="sort('stop_point')">
                                        End Point  <i v-if="sortKey == 'stop_point' " :class="[  sortDir == 1 ? 'fa-arrow-up' : 'fa-arrow-down', 'fa' ]"></i>
                                    </div>
                                </th>
                                <th>Delay at end</th>
                                <th>Export</th>
                                <th></th>
                            </tr>   
                        </thead>
                        <tbody>
                            <tr v-for="m in test_methods">
                                <td class="uk-text-center"><i class="fa  fa-sign-out fa-hover uk-link" @click="load_method(m)" uk-tooltip="Load this method into the UTM"> </i></td>
                                <td>{{ m.id }}</td>
                                <td>{{ m.type.toUpperCase() }}</td>
                                <td>{{ m.control_type.toUpperCase() }}</td>
                                <td>{{ m.control_point }} {{ m.control_type.speed ?  'mm/s' : '/s' }}</td>
                                <td>{{ m.stop_type.toUpperCase() }}</td>
                                <td>{{ m.stop_point }}</td>
                                <td>{{ m.delay }} s</td>
                                <td class="uk-text-center">
                                    <a :href="'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(m))"  :download="'Materiom UTM ' + m.id + '.json'">
                                        <i class="fa fa-download fa-hover uk-link" uk-tooltip="Export this method to JSON"></i>
                                    </a>
                                </td>
                                <td class="uk-text-center"><i class="fa fa-close fa-hover uk-link" @click="delete_method(m)" uk-tooltip="Delete this method"></i></td>
                                
                            </tr>   

                        </tbody>
                    </table>
                    
                </div>
        </div>
    </div>


</div>
`
})
