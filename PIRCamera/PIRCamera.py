'''
PIR CAMERA
DESC: The PIR camera is a utilitiy used on the raspberry PI 3 to
monitor activity using a PIR sensor, reocrd video and report that activity
Author: Jonathan L Clark
Date: 11/2/2020
'''


from flask import Flask
from flask import render_template
from flask import Response
from flask import request

# creates a Flask application, named app
app = Flask(__name__)

import socket
import time
from threading import Thread
from time import sleep
from datetime import datetime
import json
import os
import RPi.GPIO as GPIO

PIR_PULSE = 16
PIR_LIGHT = 26

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme
GPIO.setup(PIR_PULSE, GPIO.IN)
GPIO.setup(PIR_LIGHT, GPIO.OUT)

app = Flask(__name__, static_url_path='/home/pi/Server/PIRCamera')
@app.route("/")
def home():
    return render_template('index.html')

@app.route("/data.json")
def ShowData():
    global pir
    jsonStr = pir.ToJson()
    return Response(jsonStr, mimetype='text/json')

@app.route('/settings.json/', methods=["GET","POST"])
def SettingsPost():
    error = ''
    print("Call")
    try:
        print(request.form["record_time"])
        print("Call2")
        return Response("OK", mimetype='text/plain')
    except Exception as e:
        print("Bad")
        return Response(str(e), mimetype='text/plain')

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

class PIRCamera:
    def __init__(self):
        GPIO.add_event_detect(PIR_PULSE, GPIO.RISING, self.MotionDetected)
        self.detections = 0
        self.video_recording = False
        self.width = 1280
        self.height = 720
        self.record_time = 10000
        self.fps = 25

    # Converts the data in this class to a json string
    def ToJson(self):
        dictionary = {"detections" : self.detections, "recording" : self.video_recording,
                      "width"      : self.width,      "height" : self.height,
                      "record_time" : self.record_time, "fps" : self.fps}
        jsonStr = json.dumps(dictionary)

        return jsonStr
        
    # Records a video
    def RecordVideo(self):
        self.video_recording = True
        GPIO.output(PIR_LIGHT, GPIO.HIGH)
        print("Recording video...")
        now = datetime.now() # current date and time
        file_name = now.strftime("/home/pi/Videos/%m_%d_%Y_%H_%M_%S_sec")
        command = "raspivid -vf -t " + str(self.record_time) + " -w " + str(self.width) + " -h " + str(self.height) + " -fps " + str(self.fps) + " -b 1200000 -p 0,0," + str(self.width) + "," + str(self.height) + " -o " + file_name + ".h264"
        os.system(command)
        os.system("MP4Box -add " + file_name + ".h264 " + file_name + ".mp4")
        os.system("rm " + file_name + ".h264")
        print("Video finished")
        GPIO.output(PIR_LIGHT, GPIO.LOW)
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
    app.run(host='0.0.0.0', port=80, debug=True)
    while (True):
        time.sleep(1)
    shutdown_server()
