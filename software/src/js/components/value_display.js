Vue.component('value-display', {
    props: [ "name","units","value","zeroable"],
    data: function(){
        return {
            

        }
    },
    computed:{

    },
    methods:{
        change_units: function(){
            this.$emit("change-units")
            }
    },
    template:`
   
<div class="uk-width-1-1 uk-padding-small uk-background-default uk-flex uk-flex-column uk-flex-between bordered">

    <div class="uk-width-1-1 uk-flex uk-flex-inline uk-flex-between">
        <div class="uk-text-center" style="font-size:1.2em; font-weight: 600">
        {{name}}
        </div>
        <div v-if="zeroable" class="uk-button uk-button-primary uk-button-small" uk-tooltip="Zero this reading" @click="$emit('zero')">Zero</div>
    </div>
    <div class="uk-width-1-1 uk-flex uk-flex-inline uk-flex-middle uk-flex-between">
        
        <div style="font-size: 2.5em;" v-if="units=='bits'">
            {{value.toFixed(0)}}
        </div>
        <div style="font-size: 2.5em;" v-else-if="units=='g'">
            {{value.toFixed(1)}}
        </div>
        <div style="font-size: 2.5em;" v-else>
            {{value.toFixed(3)}}
        </div>
        
        <div @click="change_units" style="cursor:pointer">
            {{units}}
        </div>
    </div>

</div>
`
})
