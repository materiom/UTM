
Vue.component('results', {
    props: [ "name","units","value","zeroable"],
    data: function(){
        return {
            folder:'./data',
            tests: [],
            selectedTests:[]
            
        }
    },
    computed:{
        
    },
    mounted:function(){
        console.log("GETTING TESTS")
        this.getTests()
    },
    methods:{
        
        getTests: function(){
            console.log("GETTING TESTS FUNCTION")
            var self = this
            try {
                
                let tests_file = fs.readFileSync(`${self.folder}/tests.db`, "utf8")
                let tests = tests_file.split("\n")
                tests = tests.filter(t=> t != "")

                self.tests = JSON.parse( `[${tests.join(",")}]` )
               
                self.tests = self.tests.map( t => {
                    t.active = false
                    t.visible = true
                    return t
                })
                
                
            }
            
            catch(err){
                    console.log(err)
            }
        },
        toggleSelection: function(idx){
            var self = this
            //console.log(this.tests[idx])
            this.tests[idx].active = this.tests[idx].active ? false : true
    
            self.selectedTests = this.tests.filter(t => t.active == true)
            console.log(self.selectedTests.length)
            self.$refs.plot1.render()
            self.$refs.plot2.render()
    
           
        }
        
    },
    template:`   
<div class="uk-width-1-1 uk-grid-small" uk-grid>
        <div class="uk-width-1-2" style="height: 85vh;overflow-y:scroll">
            <div>   
                <table class="uk-table uk-table-small uk-table-hover">
                    <thead>
                        <tr>
                            <th>Date/Time</th>
                            <th>ID</th>
                            <th>Method</th>
                            <th>Sample</th>
                            <th>Material</th>
                            <th>Export</th>
                        </tr>
                    </thead>
                    <tbody v-if="tests.length > 0">
                        <tr v-for="(t,i) in tests" @click="toggleSelection(i)" :class="[ t.active == true ? 'active':'']">
                            <td>{{t.date}} {{t.start_time}}</td>
                            <td>{{t.id}}</td>
                            <td>{{t.method.id}}</td>
                            <td>{{t.sample.id}}</td>
                            <td>{{t.sample.material.name}}</td>
                            <td>
                                <div>
                                    <a :href="'/data/'+ t._id +'_finished.csv'" download>
                                        <i class="fa fa-download"></i>
                                    </a>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
                <div  class="uk-width-1-1 uk-text-large uk-text-center" v-if="tests.length == 0">
                    No tests found
                </div>
            </div>
        </div>

        <div class="uk-width-1-2">
        <div>
            <div class="uk-padding-small">
                 <ul uk-switcher animation="uk-animation-fade" uk-tab>
                    <li class="uk-active"><a>Load - Displacement</a></li>
                    <li><a>Stress - Strain</a></li>
                </ul>

                    <ul class="uk-switcher">
                        <li>
                            <div
                                is="static-plot"
                                ref="plot1"
                                :tests=selectedTests
                                chartType="line"
                                xlabel="Displacement (mm)"
                                ylabel="Load (kN)"
                                xkey="disp_rel"
                                ykey="load_rel"
                                xfmt=".2f"
                                yfmt=".2f"
                            ></div>

                        </li>
                        
                        
                        <li>
                            <div
                                is="static-plot"
                                ref="plot2"
                                :tests=selectedTests
                                chartType="line"
                                xlabel="Strain (mm/mm)"
                                ylabel="Stress (MPa)"
                                xkey="strain_eng"
                                ykey="stress_eng"
                                xfmt=".2f"
                                yfmt=".2f"
                            ></div>

                        </li>
                    </ul>
              
            </div>
        </div>
        
        </div>
        

</div>
`
})
