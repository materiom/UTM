from PyQt5 import QtWidgets, QtCore
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import sys  # We need sys so that we can pass argv to QApplication
import os
import time
from threading import Thread

from controller import Controller





class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.setGeometry(0, 0, 1200, 1000)
        self.setWindowTitle("UTM Controller - Monitoring Utility")

        
        
        
        self.mainWin = pg.GraphicsLayoutWidget()
      
       
        self.graph_disp = self.mainWin.addPlot(title="Extensometer: Displacement (mm) and Speed (mm/s)")
        
        self.setCentralWidget(self.mainWin)
        
        

        self.y_disp = []  # disp
        self.x = []  # time
        #self.graph_disp.setBackground('k')
        #self.graph_disp.addLegend()
        
        #self.graph_load.setBackground('k')
        #self.graph_load.addLegend()

        pen0 = pg.mkPen(color=(255, 0, 0))
        pen1 = pg.mkPen(color=(100, 100, 255))
        
        
        self.data_line_disp =  self.graph_disp.plot(self.x, self.y_disp, pen=pen0, name="Displacement")
        
        self.controller = Controller().init()
        
        
        t = Thread(target=self.get_user_input, args=[])
        t.daemon = True
        t.start()
        
         

        self.timer = QtCore.QTimer()
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.update_plots)
        self.timer.start()

       

    def get_user_input(self):
        
        while True:
            cmd = input("Enter controller command and press Return:\n")
            if cmd:
                try:
                    cmd = cmd.split(":")
                    if cmd[0] == "speed":
                        self.controller.set_actuator_speed(float(cmd[1]))
                        print(f"CMD to write to Arduino: {cmd}")
                    elif cmd[0] == "dir":
                        self.controller.set_actuator_direction(int(cmd[1]))
                        print(f"CMD to write to Arduino: {cmd}")
                    elif cmd[0] == "led":
                        self.controller.set_led_brightness(int(cmd[1]), float(cmd[2]))
                        print(f"CMD to write to Arduino: {cmd}")
                    elif cmd[0] == "enable":
                        self.controller.motor.enable()
                        print(f"Motor enabled")
                    elif cmd[0] == "disable":
                        self.controller.motor.disable()
                        print(f"Motor disabled")
                    else:
                        print("Sorry, command not recognised. Please try again...")
                    time.sleep(0.01)
                    #self.controller.motor.readI2C()
                    
                except BaseException as err:
                    print(err)



    def update_data(self):
        data = self.controller.get_values()
        print(data)
        
        self.x.append(float(data["time"])) 
        self.y_disp.append(float(data["displacement_abs"]))
      
        
        if len(self.x) > 500:
            self.x = self.x[1:]  # Remove the first x element.
            self.y_disp = self.y_disp[1:]  # Remove the first x element.

    def update_plots(self):
        
        self.update_data()
        
        self.data_line_disp.setData(self.x, self.y_disp)  # Update the data.




if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet("QLabel{font-size:30px}")
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
