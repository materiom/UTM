from picamera2 import Picamera2
import base64
import libcamera
import sys
import io
import struct
import time
import json
import zmq
import cv2
import numpy as np
from queue import Queue
from collections import deque
from threading import Thread
import atexit


# user defined machine vision function
#from machine_vision import edge_mv


font                   = cv2.FONT_HERSHEY_SIMPLEX
fontScale              = 1.5
fontColor              = 180
thickness              = 2
lineType               = 2



def addTextOverlay(frame:np.ndarray, msg:str):
        
        newFrame = cv2.putText(frame,
                msg, 
                ( 10  , frame.shape[0]-18 ), 
                font, 
                fontScale,
                fontColor,
                thickness,
                lineType)

        return newFrame





class VideoExtensometer:
        def __init__(self, bufferSize=1024):
                """ Setup sockets to stream an image to the frontend """
                self.zmqCtx = zmq.Context()
                self.socket = self.zmqCtx.socket(zmq.PUB)
                self.socket.bind('ipc://camera.ipc') # Socket ipc path. NOT this script

                """ Setup the buffer queue """
                self.Q = Queue(maxsize=bufferSize)
                
                
                
                
                self.stopped = True
                
                
                
                
                
                
                
                self.connected = False
                self.frame = None

                self.measurements = deque(maxlen=bufferSize)

                self.p_dist = 0.0 # point distance
                self.scale_px = 0.06125 # Scale factor to convert pixels to mm units


                # ======
                # Setting flags that can be changed on the fly to affect the streaming of frames
                # =======
                self.isSaving = False # Used to flag whether to write the images to local disk
                self.isPreview = True # Streaming preview frames
                self.isStreaming = True # Streaming full frames

                
                self.init()


        def init(self):
                
                """ Set up the camera """
                self.camera = Picamera2()
                self.height = 720
                self.width = 1280
                self.config = self.camera.create_video_configuration({"size": (self.width,self.height), "format":"RGB888"})
                print(self.config)
                self.config["controls"] = {}
                #self.config["transform"] = libcamera.Transform(hflip=1, vflip=1)
                self.config["controls"]["FrameRate"] = 30.0
                #self.config["controls"]["AnalogueGain"] = 1.0
                #self.camera["controls"]["ColourGains"] = 1.0
                self.config["controls"]["AwbEnable"] = 0 # Auto White Balance
                self.config["controls"]["AeEnable"] = 0 # Auto Exposure enable
                self.config["controls"]["ExposureTime"] = 1000
                
                #self.config["controls"]["NoiseReductionMode"] = 1
                
                self.camera.configure(self.config)
                #self.camera.start_preview()
                




        def start(self):
                # start the thread to read frames from the video stream
                self.camera.start()
                
                self.camera.led = True
                time.sleep(1.0)
                
                
                t1 = Thread(target=self.update, args=())
                t1.daemon = True
                t1.start()
                
                
                t2 = Thread(target=self.stream, args=())
                t2.daemon = True
                t2.start()
                return self



        def update(self):
                # keep looping infinitely until the thread is stopped

                while True:
                        
                        frame = self.camera.capture_array() # RGB888 format (3 elements per pixel)
                        
                        # Rotate frame 90 degrees
                        frame = np.rot90(frame)
                        
                        self.frame = frame
                        
                        #self.Q.put(frame)
                        time.sleep(0.05)




        def stream(self):
                # start the thread to read frames from the video stream
                #print("Sending preview frame")
                while True:
                        try:
                                #frame = self.read()
                                frame = self.frame
                                self.p_dist, frame = self.measure(frame)
                                if not frame is None:
                                        
                                        self.frame = frame
                                        self.connected = True
                                        frame = cv2.resize(frame, (0,0), fx=0.4, fy=0.4)

                                        # Low quality encoding for the preview image. Again this saves bandwidth and CPU load.
                                        _, buff = cv2.imencode(".jpg", frame, [ int(cv2.IMWRITE_JPEG_QUALITY), 90 ])
                                        
                                        # publish the preview frame base64 string to the zeromq socket
                                        self.socket.send( buff.tobytes() )
                                
                        except BaseException as err:
                                self.connected = False
                                print(err)
                                pass
                                
                        time.sleep(0.05)

                return self



        def measure(self, frame):
                """
                     Measure the displacements between the detected points
                """
                
                try:
                        # Make it grayscale
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                     
                        
                        # Threshold the image to segment the dark dots on a bright background (THRESH_BINARY_INV)
                        
                        ret, thresh = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY_INV )
                        
                        ## Find the dots! The detected dots will now be white on a black background.
                        cnts, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2:]
                        
                        # Set limits for how small/large a dot can be for it to be considered as a legitimate sample marking
                        AREA_THRESHOLD_MIN , AREA_THRESHOLD_MAX  = (50 , 4000)

                        plist = []

                        for c in cnts:
                                area = cv2.contourArea(c) # Calculate the contour area
                                if area > AREA_THRESHOLD_MIN and area < AREA_THRESHOLD_MAX:
                                        (x, y), radius = cv2.minEnclosingCircle(c) # Use "minEnclosingCircle" to find the middle of the dot
                                        plist.append( [ float(x), float(y) ]) # Save the dot centroid coordinates to be used for distance measurements
                                
                                        #cv2.circle(frame, (int(x), int(y)), int(radius), 200, 3)

                        if len(plist) == 2: # only do this if there are two points detected
                                plist = np.array(plist)
                                # Calculate the distance between the two detected points
                                dist = np.sqrt( np.diff(plist[:,0])**2 + np.diff(plist[:,1])**2)[0] 
                                dist = dist * self.scale_px
                                
                                
                                
                                
                                # Add overlays to show the dot measurements
                                gray = addTextOverlay(gray, f"{dist:.3f} mm") # Overlay the number of detected dots on the image frame
                                
                                #"""
                                gray = cv2.line(gray, (int(plist[0][0]),int(plist[0][1])), (int(plist[1][0]),int(plist[1][1])), 150 ,3)
                                w = 10
                                gray[int(plist[0][1]),int(plist[0][0])-w:int(plist[0][0])+w] = 150
                                gray[int(plist[1][1]),int(plist[1][0])-w:int(plist[1][0])+w] = 150
                                #"""
                                
                                
                        else: # More or less than 2 dots have been detected so we don't know which ones are the correct ones. Don't do anything
                                dist = None
                            
                       
                        
                        return dist, gray # Sample length, frame with overlays
                
                except BaseException as err:
                        pass
                        return None, None
        




        def prepare_folder(self):
                """
                ensure there is a folder to save the images in
                """
        
        
                return self





        def save_image(self, frame:np.ndarray):
                """
                    saves an image during data logging
                """
                
                
                return self






        def read(self):
                # return next frame in the queue
                #print(self.Q.qsize())
                if self.more():
                        return self.Q.get()
                else:
                        return None
        
        
        def more(self):
                # return True if there are frames in the queue
                if self.Q.qsize() > 0:
                        return True
                else:
                        return False
    
    
    
        def stop(self):
                # indicate that the thread should be stopped
                print("[INFO] Video stream thread stopping...")
                self.stopped = True
                self.camera.led = False
                self.camera.close()


        def close(self):
                try:
                        self.socket.close()
                        self.zmq_ctx.term()
                        print("Closed zmq sockets")
                except BaseException as err:
                        print(err)

                try:
                        self.camera.close()
                except BaseException as err:
                        print(err)
    







def main():
        stream = VideoExtensometer().start()

        #print("[INFO] pausing for 1.0 second...")
        #time.sleep(1.0)
    
        while True:
                #pass

        #"""  
                frame = stream.frame
                if not frame is None:
                        #print(frame)
                        cv2.imshow('test', frame)
                        cv2.waitKey(1)


        stream.stop()
        cv2.destroyAllWindows()
        
        #"""


if __name__ == "__main__":
        main()
