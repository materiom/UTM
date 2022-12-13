Vue.component('live-plot', {
    props:[
        "livedata",
        "xlabel",
        "ylabel",
        "xkey",
        "ykey",
        "xfmt",
        "yfmt",
        "debug",
        "testing"
    ],
    data: function(){
        return {
            start: 0,
            chart: {
                scales: {},
                axes:{},
                canvas: undefined,
                overlay: undefined,
                ctx: undefined,
                overlay_ctx: undefined,
                width: 800,
                height: 220
            },
            keyname: undefined,
            pData: [],
            line: undefined,
            pCount: 0,
            rollchart: false,
			rollwinsecs: 10,
            fixAxis: {
                x: false,
                y: false
            },
            scatter_colour: undefined,
            scatterPointSize: 4,
            scatterColourMin: undefined,
            scatterColourMax: undefined,
            axisRange: {
                x: [-30,220],
                y: [-6,6]

            }

        }
    },
    created: function(){
        this.keyname = this.ykey
        this.x = this.xkey
        this.y = this.ykey
    },
    mounted: function(){
        let self = this
        this.init();
        
    },
    watch:{
        immediate: true,
        deep: true,
        livedata: function(newData){
            let self = this
            if(self.debug == true || self.testing){
                this.pData.push(newData)
            }
        }
    },
    computed:{
       

    },
    methods:{
        init: function(){
            let self = this
            self.chart.width = 800
            self.chart.height = 600
           
            self.chart.canvas = d3.select( self.$refs.plot_canvas ) // Select canvas element
            // Set canvas dimensions
            self.chart.canvas.attr('width', self.chart.width)
            self.chart.canvas.attr('height', self.chart.height)

            self.chart.ctx = self.chart.canvas.node().getContext('2d', { alpha: false }) // Get chart context for drawing

            // Set default canvas draw colours 
            self.chart.ctx.fillStyle = '#f11'
            self.chart.ctx.strokeStyle = '#f11'


            // Initiliase the pverlay canvas - used to track and display mouseover events 
            self.chart.overlay = d3.select(self.$refs.overlay_canvas)
            self.chart.overlay.attr('width', self.chart.width)
            self.chart.overlay.attr('height', self.chart.height)
            self.chart.overlay_ctx = self.chart.overlay.node().getContext('2d',{ alpha: true })
           

            // Initiliase X axis scale
            self.chart.scales.x = d3.scaleLinear()
                                    .domain([0,1])
                                    .range([60, self.chart.width - 20])
                                    .nice()

            // Initiliase Y axis scale
            self.chart.scales.y = d3.scaleLinear()
                                    .domain([0,1])
                                    .range([self.chart.height - 50, 10])
                                    .nice()
            

            // Do initial draw of the data
            self.render()
    
        },
        render: function(){
            let self = this

            // Clear the canvas for the next render cycle
            self.chart.ctx.fillStyle = '#fff'
            self.chart.ctx.fillRect(0,0,self.chart.width,self.chart.height)

            // Reset stroke style as the axes change it to red
            self.chart.ctx.fillStyle = '#f11'
            self.chart.ctx.strokeStyle = '#f11'

            self.chart.overlay_ctx.strokeStyle = '#f11'

            if(this.pData.length > 1){
                // calculate the new scales
                
                // X Axis
                if(self.fixAxis.x == true){
                    self.chart.scales.x.domain([self.axisRange.x[0], self.axisRange.x[1]])
                }
                else {
                    self.chart.scales.x.domain(d3.extent(self.pData, function(d){ return d[self.xkey] }))
                }
                
                // Y Axis
                if(self.fixAxis.y == true){
                    self.chart.scales.y.domain([self.axisRange.y[0], self.axisRange.y[1]])
                }
                else{ 
                    self.chart.scales.y.domain(d3.extent(self.pData, function(d){ return d[self.ykey] }))
                }


                // Move to the first point on the path to be plotted - ie the current livedata values
                this.chart.ctx.moveTo( this.chart.scales.x(self.pData[self.pData.length-1][self.xkey]), this.chart.scales.y(self.pData[self.pData.length-1][self.ykey]) )
                
                // start a new path - ie line on the plot
                this.chart.ctx.beginPath()
            
                // Now this bit actually plots the rest of the data
                this.pData.forEach( (d,i) => {
                    self.chart.ctx.lineTo(self.chart.scales.x(d[self.xkey]), self.chart.scales.y(d[self.ykey]), 2, 2)
                })

                // Finish the stroke to finish plotting the line
                this.chart.ctx.stroke()
                
                this.chart.ctx.fillStyle = '#11f'
                this.chart.ctx.strokeStyle = '#11f'
                x = this.chart.scales.x(self.livedata[self.xkey])
                y = this.chart.scales.y(self.livedata[self.ykey])
                this.chart.ctx.fillRect(x, y, 4,4);

                
                
            
            }
            
           

            drawXaxis(
                    self.chart.ctx,
                    self.chart.scales.x,
                    self.xlabel,
                    self.chart.height-50,
                    [60,self.chart.width-20],
                    self.xfmt
                )



            drawYaxis(
                    self.chart.ctx,
                    self.chart.scales.y,
                    self.ylabel,
                    60,
                    [self.chart.height-50,10],
                    self.yfmt
                )
         
                
            window.requestAnimationFrame(self.render) // Recursively call the render function on the next tick of the window renderer function ( 60 fps ? )

        },
        overlayTooltip: function(evt){
            //console.log(evt)
            // evt.layerX and evt.layerY are the correct values to send to the inverse scale functions
            xval = this.chart.scales.x.invert(evt.layerX)
            yval = this.chart.scales.y.invert(evt.layerY)
            //console.log(xval, yval)
        }
        



    },
    template:`
    <div style="padding: 4px">
        <div class="uk-width-1-1 uk-flex uk-flex-inline uk-flex-end">

            <button class="uk-button uk-button-small" uk-tooltip="title:Open chart settings; delay:500"><i class="fa fa-cog"></i></button>

            <div uk-dropdown="mode: click">
            
            <table class="uk-width-1-1"> 
                    <tr>
                        <td>Fixed X Axis</td>
                        <td><input type="checkbox" v-model="fixAxis.x" /></td>
                    </tr>
                    <tr>
                        <td>X min</td>
                        <td><input type="number" step=1 :max="axisRange.x[1]-1" v-model="axisRange.x[0]" /></td>
                    </tr>
                    <tr>
                        <td>X max</td>
                        <td><input type="number" step=1 :min="axisRange.x[0]+1"  v-model="axisRange.x[1]" /></td>
                    </tr>

                    <tr>
                        <td>Fixed Y Axis</td>
                        <td><input type="checkbox" v-model="fixAxis.y" /></td>
                    </tr>
                    <tr>
                        <td>Y min</td>
                        <td><input type="number" step=1 :max="axisRange.y[1]-1" v-model="axisRange.y[0]" /></td>
                    </tr>
                    <tr>
                        <td>Y max</td>
                        <td><input type="number" step=1 :min="axisRange.y[0]+1"  v-model="axisRange.y[1]" /></td>
                    </tr>   

                </table>

               
            </div>    



        </div>
        
        <div class="canvasContainer" style="padding-top:40px">
            <canvas ref="plot_canvas" height=600 width=600></canvas>
            <canvas ref="overlay_canvas" height=600 width=600 @mousemove="overlayTooltip"></canvas>
        </div>
    </div>
    `
})


///////
// Draw axes code from
// https://observablehq.com/@spattana/drawing-axis-in-d3-canvas
/////

drawXaxis = (context, xScale, label, Y, xExtent, fmt) => {
    const [startX, endX] = xExtent;
    let tickSize = 6,
      xTicks = xScale.ticks(10); // You may choose tick counts. ex: xScale.ticks(20)
      xTickFormat = xScale.tickFormat(); // you may choose the format. ex: xScale.tickFormat(tickCount, ".0s")
  
    context.strokeStyle = "#222";
  
    context.beginPath();
    xTicks.forEach(d => {
        context.moveTo(xScale(d), Y);
        context.lineTo(xScale(d), Y + tickSize);
    });
    context.stroke();
  
    context.beginPath();
    context.moveTo(startX, Y + tickSize);
    context.lineTo(startX, Y);
    context.lineTo(endX, Y);
    context.lineTo(endX, Y + tickSize);
    context.stroke();
  
    context.textAlign = "center";
    context.textBaseline = "top";
    context.font = "18px BrandonGrotesque";
    context.fillStyle = "#222";
    xTicks.forEach(d => {
        context.beginPath();
        context.fillText(xTickFormat(d), xScale(d), Y + tickSize);
    });
    context.font = "22px BrandonGrotesque";
    context.fillText(label, (xExtent[1] - xExtent[0])*0.6, Y+30);
  }



drawYaxis = (context, yScale, label, X, yExtent, fmt) => {
    const [startY, endY] = yExtent;
  
    const tickPadding = 3,
      tickSize = 6,
      yTicks = yScale.ticks(8),
      yTickFormat = yScale.tickFormat();
  
    context.strokeStyle = "#222";
    context.beginPath();
    yTicks.forEach(d => {
        context.moveTo(X, yScale(d));
        context.lineTo(X - tickSize, yScale(d));
    });
    context.stroke();
  
    context.beginPath();
    context.moveTo(X - tickSize, startY);
    context.lineTo(X, startY);
    context.lineTo(X, endY);
    context.lineTo(X - tickSize, endY);
    context.stroke();
  
    context.textAlign = "right";
    context.textBaseline = "middle";
    context.font = "18px BrandonGrotesque";
    context.fillStyle = "#222";
    yTicks.forEach(d => {
        context.beginPath();
        context.fillText(yTickFormat(d), X - tickSize - tickPadding, yScale(d));
    });
    
    context.save();
    context.translate(-8, yExtent[0]/2);
    context.rotate(-Math.PI/2);
    context.textAlign = "center";
    context.font = "22px BrandonGrotesque";
    context.fillText(label, 20, 20);
    context.restore();
    

  }





















  Vue.component('static-plot', {
    props:[
        "tests",
        "chartType",
        "xlabel",
        "ylabel",
        "xkey",
        "ykey",
        "xfmt",
        "yfmt"
    ],
    data: function(){
        return {
            start: 0,
            chart: {
                scales: {},
                axes:{},
                canvas: undefined,
                overlay: undefined,
                ctx: undefined,
                overlay_ctx: undefined,
                width: 800,
                height: 600           
            },
            keyname: undefined,
            line: undefined,
            pCount: 0,
            rollchart: false,
			rollwinsecs: 10,
            fixAxis: {
                x: false,
                y: false
            },
            scatter_colour: undefined,
            scatterPointSize: 4,
            scatterColourMin: undefined,
            scatterColourMax: undefined,
            axisRange: {
                x: [0,1],
                y: [0,1]

            }

        }
    },
    created: function(){
        this.keyname = this.ykey
        this.x = this.xkey
        this.y = this.ykey
    },
    mounted: function(){
        let self = this
    
        this.init();
        
    },
    activated: function(){
        
    },
    computed:{
       

    },
    methods:{
        init: function(){
            let self = this

            if(this.charttype == "timeseries" || this.charttype == "line"){
                self.chart.width = 800
                self.chart.height = 600
            }
            else if(this.charttype == "scatter"){
                self.chart.width = 600
                self.chart.height = 600
                
            }

            self.chart.canvas = d3.select( self.$refs.plot_canvas )
            //console.log(self.chart.canvas)
            self.chart.canvas.attr('width', self.chart.width)
            self.chart.canvas.attr('height', self.chart.height)
            self.chart.ctx = self.chart.canvas.node().getContext('2d', { alpha: false })
            self.chart.ctx.fillStyle = '#f11'
            self.chart.ctx.strokeStyle = '#f11'


            self.chart.overlay = d3.select(self.$refs.overlay_canvas)
            self.chart.overlay.attr('width', self.chart.width)
            self.chart.overlay.attr('height', self.chart.height)
            self.chart.overlay_ctx = self.chart.overlay.node().getContext('2d',{ alpha: true })
           



            self.chart.scales.x = d3.scaleLinear()
                                    .domain([0,20])
                                    .range([60, self.chart.width - 20])
                                    .nice()


            self.chart.scales.y = d3.scaleLinear()
                                    .domain([0,0.5])
                                    .range([self.chart.height - 50, 10])
                                    .nice()
            
            self.chart.scales.colour = d3.scaleSequential(d3.interpolateSpectral)
                                            .domain([0,10])
            

            self.render()
    
        },
        getTestData: function(test_id){
            //console.log(test_id)
            // Get the test CSV file
            filepath = `./data/${test_id}.csv`
            file = fs.readFileSync(filepath, "utf8")
            dataArray = file.split("\n")
            
            headers = dataArray[0].split(",")
            //console.log(headers)
            
            data = []
            
            // Read it into a JSON object
            dataArray.forEach((d,i) => {
                    if(i > 0){
                            rowArray = dataArray[i].split(",");
                            row = {}
                            headers.forEach((h,j) => {
                                row[h] = +rowArray[j]     
                            })
                        data.push(row)
                    } 
            })
            
            // Return the data object to be plotted
            
            
            return data
        },
        render: function(){
            
            let self = this
       
            self.chart.ctx.fillStyle = '#fff'
            self.chart.ctx.fillRect(0,0,self.chart.width,self.chart.height)


                
            // Reset stroke style as the axes change it to black
            self.chart.ctx.fillStyle = '#f11'
            self.chart.ctx.strokeStyle = '#f11'

            self.chart.overlay_ctx.strokeStyle = '#111'



            self.chart.scales.x.domain([self.axisRange.x[0], self.axisRange.x[1]])
            self.chart.scales.y.domain([self.axisRange.y[0], self.axisRange.y[1]])
           

            // Define xrange
            let xrange = [0,1]
            
            // Define yrange
            let yrange = [0,1]
        
            var tests = self.tests

            tests.forEach( (t,i) => {
                
                
                if(t.active == true && t.visible == true){
                
                    tests[i].data = self.getTestData(t._id)
                    
                    var xExt = d3.extent(tests[i].data, function(d){ return d[self.xkey] })
                    var yExt = d3.extent(tests[i].data, function(d){ return d[self.ykey] })
                    
                    
                    if(xExt[0] < xrange[0]){ xrange[0] = xExt[0]  }
                    if(xExt[1] > xrange[1]){ xrange[1] = xExt[1]  }
                    if(yExt[0] < yrange[0]){ yrange[0] = yExt[0]  }
                    if(yExt[1] > yrange[1]){ yrange[1] = yExt[1]  }
                    
                    self.chart.scales.x.domain(xrange)
                    self.chart.scales.y.domain(yrange)
                    
                    
                
                }
                
                
            })
            
            let cScale = d3.interpolateSpectral
            
            
            tests.forEach( (t,i) => {
                console.log(cScale(i))
                
                if(t.active == true && t.visible == true){
                
                    let data = t.data
                  
                    if(data.length > 1){
                        this.chart.ctx.moveTo(self.chart.scales.x(data[0][self.xkey]), self.chart.scales.y(data[0][self.ykey]))
                        self.chart.ctx.fillStyle = cScale(i/tests.length)
                        self.chart.ctx.strokeStyle = cScale(i/tests.length)
                        this.chart.ctx.beginPath();
                        
                        data.forEach( (d,i) => {
                            self.chart.ctx.lineTo(self.chart.scales.x(d[self.xkey]), self.chart.scales.y(d[self.ykey]), 3)
                        })
                        
                        this.chart.ctx.stroke()
                    }
                
                }
                
                
            })
            
                
                
                    
                drawXaxis(
                    self.chart.ctx,
                    self.chart.scales.x,
                    self.xlabel,
                    self.chart.height-50,
                    [60,self.chart.width-20],
                    self.xfmt
                )



            drawYaxis(
                    self.chart.ctx,
                    self.chart.scales.y,
                    self.ylabel,
                    60,
                    [self.chart.height-50,10],
                    self.yfmt
                )
                
            
           

          


        },



        overlayTooltip: function(evt){
            //console.log(evt)
            // evt.layerX and evt.layerY are the correct values to send to the inverse scale functions
            xval = this.chart.scales.x.invert(evt.layerX)
            yval = this.chart.scales.y.invert(evt.layerY)
            //console.log(xval, yval)
        }
        



    },
    template:`
    <div style="padding: 4px">
        <div class="canvasContainer">
            <canvas ref="plot_canvas" height="400" width="600"></canvas>
            <canvas ref="overlay_canvas" height="400" width="600" @mousemove="overlayTooltip"></canvas>
        </div>
    </div>
    `
})
