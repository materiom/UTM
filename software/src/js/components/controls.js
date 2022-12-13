
Vue.component('test-controls', {
    props:['running', 'paused', 'status'],
    methods:{
        startTest: function(){
          return this.$emit("start")
        },
        pauseTest: function(){
              return this.$emit("pause")
        },
        resumeTest: function(){
              return this.$emit("resume")

        },
        stopTest: function(){
              return this.$emit("stop")
        }
    },
    template: `
    <div class="uk-width-1-1 uk-flex uk-flex-inline">

      <div class="uk-width-expand uk-flex uk-flex-middle">
          <div class="uk-button uk-button-danger" v-if="running || paused " @click="stopTest" uk-tooltip="Completely stop and reset the test"> Stop Test <i class="fa fa-stop"></i></div>
          <div class="uk-button uk-button-primary" v-if="paused && !running" @click="resumeTest" uk-tooltip="Resume test from this point"> Resume Test  <i class="fa fa-play"></i></div>
          <div class="uk-button uk-button-primary" v-if="running && !paused" @click="pauseTest" uk-tooltip="Pause test to be restarted"> Pause Test  <i class="fa fa-pause"></i></div>
          <div :class="[ status.test_ready  ? 'uk-button-success': 'uk-button-disabled' ,'uk-button']" v-if="!running && !paused" @click="startTest" :uk-tooltip="[ status.test_ready  ? 'Initiate test': 'Test not ready to run']"> {{status.test_ready  ? 'Start Test': 'Test disabled'}}  <i class="fa fa-play"></i></div>
      </div>
    <div class="uk-width-auto uk-grid-small uk-flex-between uk-flex-middle bordered" @click="$emit('get-status')" uk-grid>
           
          <div>
              <div class="uk-flex uk-flex-column uk-text-center">
                  <div :style="{ 'color' :   status.controller ? 'var(--main-green-active)' : 'var(--main-red-dark)' }"  :uk-tooltip="status.controller ? 'Active' : 'Not connected'">
                      <i class="fa fa-microchip"></i>
                  </div>
                  <div style="font-size: 0.8em;">
                      Controller
                  </div>
              </div>
          </div>
          <div>
              <div class="uk-flex uk-flex-column uk-text-center">
                  <div :style="{ 'color' :   status.motor ? 'var(--main-green-active)' : 'var(--main-red-dark)' }"  :uk-tooltip="status.motor ? 'Active' : 'Not running'">
                      <i :class="[ status.motor_moving ? 'fa-spin' : '', 'fa','fa-gear']"></i>
                  </div>
                  <div style="font-size: 0.8em;">
                      Motor
                  </div>
              </div>
          </div>
          <div>
              <div class="uk-flex uk-flex-column uk-text-center">
                  <div :style="{ 'color' :   status.load_cell ? 'var(--main-green-active)' : 'var(--main-red-dark)' }" :uk-tooltip="status.load_cell ? 'Active' : 'Not connected'">
                      <i class="fa fa-hourglass" ></i>
                  </div>
                  <div style="font-size: 0.8em;">
                      Load Cell
                  </div>
              </div>
          </div>
          <div>
              <div class="uk-flex uk-flex-column uk-text-center">
                  <div :style="{ 'color' :   status.digital_extensometer ? 'var(--main-green-active)' : 'var(--main-red-dark)' }" :uk-tooltip="status.digital_extensometer ? 'Active' : 'Not connected'">
                      <i class="fa fa-arrows-v" ></i>
                  </div>
                  <div style="font-size: 0.8em;">
                      Extensometer
                  </div>
              </div>
          </div>
          <div>
              <div class="uk-flex uk-flex-column uk-text-center">
                  <div :style="{ 'color' :   status.video_extensometer ? 'var(--main-green-active)' : 'var(--main-red-dark)' }" :uk-tooltip="status.video_extensometer ? 'Active' : 'Not connected'">
                      <i class="fa fa-video-camera" ></i>
                  </div>
                  <div style="font-size: 0.8em;">
                      VideoExtens.
                  </div>
              </div>
          </div>
          
          <div class="uk-width-1-1">
              <div>
                 <div class="uk-width-1-1 uk-text-center uk-background-success" v-if="status.enabled">
                    UTM Enabled
                </div>
                <div class="uk-width-1-1 uk-text-center uk-background-danger" v-else>
                    UTM Disabled
                </div>
              </div>
          </div>
          
      </div>


    </div>

    `
})

