'''
PIR CAMERA
DESC: The PIR camera is a utilitiy used on the raspberry PI 3 to
monitor activity using a PIR sensor, reocrd video and report that activity
Author: Jonathan L Clark
Date: 11/2/2020
'''

import socket
import time
from threading import Thread
from time import sleep
from datetime import datetime
import os
import RPi.GPIO as GPIO

PIR_PULSE = 16

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme
GPIO.setup(PIR_PULSE, GPIO.IN)

class PIRCamera:
    def __init__(self):
        GPIO.add_event_detect(PIR_PULSE, GPIO.RISING, self.MotionDetected)
        self.detections = 0
        self.video_recording = False
        self.width = 1280
        self.height = 720
        self.record_time = 10000
        self.fps = 25

    # Records a video
    def RecordVideo(self):
        self.video_recording = True
        print("Recording video...")
        now = datetime.now() # current date and time
        file_name = now.strftime("/home/pi/Videos/%m_%d_%Y_%H_%M_%S_sec")
        os.system("raspivid -vf -t " + str(self.record_time) + " -w " + str(self.width) + " -h " + str(self.height) + " -fps " + str(self.fps) + " -b 1200000 -p 0,0," + str(self.width) + "," + str(self.height) + " -o " + file_name + ".h264")
        os.system("MP4Box -add " + file_name + ".h264 " + file_name + ".mp4")
        os.system("rm " + file_name + ".h264")
        print("Video finished")
        self.video_recording = False

    # Handles motion getting detected
    def MotionDetected(self, pin):
        if self.video_recording:
            return
        print("Motion detected: " + str(self.detections))
        self.detections += 1
        record_thread = Thread(target = self.RecordVideo)
        record_thread.daemon = True
        record_thread.start()
		
if __name__ == '__main__':
    pir = PIRCamera()
    while (True):
        time.sleep(1)
