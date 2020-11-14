'''
PIR CAMERA
DESC: The PIR camera is a utilitiy used on the raspberry PI 3 to
monitor activity using a PIR sensor, reocrd video and report that activity
Author: Jonathan L Clark
Date: 11/2/2020
'''

from __future__ import print_function
from flask import Flask
from flask import render_template
from flask import Response
from flask import request, redirect, url_for
# Google API Stuff
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient.http import MediaFileUpload

# creates a Flask application, named app
app = Flask(__name__)

import socket
import time
from threading import Thread
from time import sleep
from datetime import datetime
from os import path
import json
import os
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
import RPi.GPIO as GPIO

SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly','https://www.googleapis.com/auth/drive.appdata', 'https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive.install']

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

@app.route('/settings.json', methods=["GET","POST"])
def SettingsPost():
    global pir
    try:
        postLines = request.data.split('\n')
        upload_video = False
        use_light = False
        for line in postLines:
            pair = line.split('=')
            if len(pair) == 2:
                key = pair[0]
                if key == "record_time":
                    pir.record_time = int(pair[1])
                elif key == "fps":
                    pir.fps = int(pair[1])
                elif key == "upload_video":
                    upload_video = True
                elif key == "use_light":
                    use_light = True
                elif key == "resolution":
                    values = pair[1].split('_')
                    if len(values) == 2:
                        pir.width = int(values[0])
                        pir.height = int(values[1])
        print("Time: " + str(pir.record_time) + " FPS: " + str(pir.fps) + " Res: " + str(pir.width) + "X" + str(pir.height))
        pir.upload_video = upload_video
        pir.use_light = use_light
        pir.SaveSettings()
        return render_template('index.html')
    except Exception as e:
        print(str(e))
        return render_template('index.html')

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
        self.upload_video = False
        self.use_light = True
        self.LoadSettings()
        self.SetupGoogleDrive()
        self.command = "raspivid -vf -t " + str(self.record_time) + " -w " + str(self.width) + " -h " + str(self.height) + " -fps " + str(self.fps) + " -b 1200000 -p 0,0," + str(self.width) + "," + str(self.height)# + " -o " + file_name + ".h264"

    # Sets up the Google drive API for remote transfers
    def SetupGoogleDrive(self):
        try:
            print("Setting up Google Drive API...")
            creds = None
            # The file token.pickle stores the user's access and refresh tokens, and is
            # created automatically when the authorization flow completes for the first
            # time.
            if os.path.exists('/home/pi/Server/PIRCamera/token.pickle'):
                with open('/home/pi/Server/PIRCamera/token.pickle', 'rb') as token:
                    creds = pickle.load(token)
            # If there are no (valid) credentials available, let the user log in.
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file('/home/pi/Server/PIRCamera/credentials.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                # Save the credentials for the next run
                with open('token.pickle', 'wb') as token:
                    pickle.dump(creds, token)

            self.service = build('drive', 'v3', credentials=creds)
            print("Google drive setup!")
        except Exception as ex:
            print("Unable to setup google drive, retrying...: " + str(ex))
            time.sleep(1)
            self.SetupGoogleDrive()
        
    # Loads settings from a file
    def LoadSettings(self):
        file_path = '/home/pi/Documents/pir_config.json'
        if path.exists(file_path):
            f = open(file_path, "r")
            data = f.read()
            dictionary = json.loads(data)
            self.width = dictionary["width"]
            self.height = dictionary["height"]
            self.record_time = dictionary["record_time"]
            self.fps = dictionary["fps"]
            self.use_light = dictionary["use_light"]
            self.upload_video = dictionary["upload_video"]
        else:
            self.SaveSettings()

    # Saves settings to a file
    def SaveSettings(self):
        fileStr = self.ToJson()
        file_path = '/home/pi/Documents/pir_config.json'
        f = open(file_path, "w")
        f.write(fileStr)
        f.close()

    # Converts the data in this class to a json string
    def ToJson(self):
        dictionary = {"detections" : self.detections, "recording" : self.video_recording,
                      "width"      : self.width,      "height" : self.height,
                      "record_time" : self.record_time, "fps" : self.fps,
                      "upload_video" : self.upload_video, "use_light" : self.use_light}
        jsonStr = json.dumps(dictionary)

        return jsonStr
        
    # Records a video
    def RecordVideo(self):
        self.video_recording = True
        if self.use_light:
            GPIO.output(PIR_LIGHT, GPIO.HIGH)
        print("Recording video...")
        now = datetime.now() # current date and time
        file_stamp = now.strftime("%m_%d_%Y_%H_%M_%S_sec")
        file_name = now.strftime("/home/pi/Videos/" + file_stamp)
        self.command = "raspivid -vf -t " + str(self.record_time) + " -w " + str(self.width) + " -h " + str(self.height) + " -fps " + str(self.fps) + " -b 1200000 -p 0,0," + str(self.width) + "," + str(self.height)
        command = self.command + " -o " + file_name + ".h264"
        os.system(command)
        os.system("MP4Box -add " + file_name + ".h264 " + file_name + ".mp4")
        os.system("rm " + file_name + ".h264")
        print("Video finished")
        if self.use_light:
            GPIO.output(PIR_LIGHT, GPIO.LOW)
        if self.upload_video:
            try:
                print("Uploading video to Google Drive...")
                file_metadata = {'name': file_stamp + '.mp4'}
                media = MediaFileUpload(file_name + ".mp4", mimetype='video/mp4')
                file = self.service.files().create(body=file_metadata,
                                            media_body=media,
                                            fields='id').execute()
                print("Video uploaded!")
            except:
                print("Video upload failed!")
            
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
        
def StartFlask():
    try:
        app.run(host='0.0.0.0', port=80, debug=False)
        
    except:
        print("Unable to start flask, restarting...")
        time.sleep(1)
        StartFlask()
        
if __name__ == '__main__':
    pir = PIRCamera()
    
    StartFlask()

    
    while (True):
        time.sleep(1)
