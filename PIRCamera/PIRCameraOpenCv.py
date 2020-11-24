'''
PIR CAMERA
DESC: The PIR camera is a utilitiy used on the raspberry PI 3 to
monitor activity using a PIR sensor, reocrd video and report that activity
Author: Jonathan L Clark
Date: 11/2/2020
'''
# sudo apt-get install libopencv-dev python-opencv (python 2.7)

from __future__ import print_function
from imutils.video import VideoStream
import imutils
import cv2
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
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
from awscrt import io, mqtt, auth, http
from awsiot import mqtt_connection_builder
import json
import os.path

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
shadow = {
  "state": { "desired": {} }
}

USER_DIR = os.path.expanduser("~")

PATH_TO_CERT = "/home/pi/.security/98f2871021-certificate.pem.crt"
PATH_TO_KEY = "/home/pi/.security/98f2871021-private.pem.key"
PATH_TO_ROOT = "/home/pi/.security/AmazonRootCA1.pem"
ENDPOINT = "a2yizg9mkkd9ph-ats.iot.us-west-2.amazonaws.com"
TOPIC = "camera/control"
CLIENT_ID = "PIRCamera_MQTT"
RANGE = 20
move_threshold = 50

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
        enabled = False
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
                elif key == "enabled":
                    enabled = True
                elif key == "resolution":
                    values = pair[1].split('_')
                    if len(values) == 2:
                        pir.width = int(values[0])
                        pir.height = int(values[1])
        print("Time: " + str(pir.record_time) + " FPS: " + str(pir.fps) + " Res: " + str(pir.width) + "X" + str(pir.height))
        pir.upload_video = upload_video
        pir.use_light = use_light
        pir.enabled = enabled
        pir.SaveSettings()
        pir.SendShadow()
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
        #GPIO.add_event_detect(PIR_PULSE, GPIO.RISING, self.MotionDetected)
        self.detections = 0
        self.video_recording = False
        self.videos_recorded_from_start = 0
        self.width = 1280
        self.height = 720
        self.record_time = 10000
        self.fps = 25
        self.upload_video = False
        self.use_light = True
        self.enabled = False
        self.LoadSettings()
        self.SetupGoogleDrive()
        self.command = "raspivid -vf -t " + str(self.record_time) + " -w " + str(self.width) + " -h " + str(self.height) + " -fps " + str(self.fps) + " -b 1200000 -p 0,0," + str(self.width) + "," + str(self.height)# + " -o " + file_name + ".h264"
        self.SetupAWS()
        self.SendShadow()
        self.motionThread = Thread(target = self.motion_detect)
        self.motionThread.daemon = True
        self.motionThread.start()
 
    def SetupAWS(self):
        self.client = AWSIoTMQTTShadowClient("PIRCamera")
        self.client.configureEndpoint("a2yizg9mkkd9ph-ats.iot.us-west-2.amazonaws.com", 8883)
        self.client.configureCredentials(PATH_TO_ROOT, PATH_TO_KEY, PATH_TO_CERT)
        self.client.configureConnectDisconnectTimeout(10)  # 10 sec
        self.client.configureMQTTOperationTimeout(5)  # 5 sec
        self.client.connect()
        self.shadow_connect = self.client.createShadowHandlerWithName("SecurityCamera", True)
        
        # Setup the MQTT endpoint
        # Spin up resources
        event_loop_group = io.EventLoopGroup(1)
        host_resolver = io.DefaultHostResolver(event_loop_group)
        client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)
        self.mqtt_connection = mqtt_connection_builder.mtls_from_path(
            endpoint=ENDPOINT,
            cert_filepath=PATH_TO_CERT,
            pri_key_filepath=PATH_TO_KEY,
            client_bootstrap=client_bootstrap,
            ca_filepath=PATH_TO_ROOT,
            client_id=CLIENT_ID,
            clean_session=False,
            keep_alive_secs=6
        )
        connect_future = self.mqtt_connection.connect()
        # Future.result() waits until a result is available
        connect_future.result()
        self.mqtt_connection.subscribe(topic=TOPIC, qos=mqtt.QoS.AT_LEAST_ONCE, callback=self.subcallback)
    
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
        
    # Generates a shadow for AWS
    def SendShadow(self):
        global shadow
        dictionary = {"detections" : self.detections, "recording" : self.video_recording,
                      "width"      : self.width,      "height" : self.height,
                      "record_time" : self.record_time, "fps" : self.fps,
                      "upload_video" : self.upload_video, "use_light" : self.use_light,
                      "enabled" : self.enabled, "videos_this_session" : self.videos_recorded_from_start}
                      
        shadow["state"]["desired"] = dictionary
        self.shadow_connect.shadowUpdate(json.dumps(shadow), self.ShadowCallback, 5)
 
    # Subscriber callback
    def subcallback(self, topic, payload, **kwargs):
        try:
            dictionary = json.loads(payload)
            if "enable" in dictionary:
                self.enabled = True
            elif "disable" in dictionary:
                self.enabled = False
            if "fps" in dictionary:
                self.fps = int(dictionary["fps"])
            if "use_light" in dictionary:
                self.use_light = dictionary["use_light"]
            if "upload_video" in dictionary:
                self.upload_video = dictionary["upload_video"]
            if "record_time" in dictionary:
                self.record_time = dictionary["record_time"]
            if "start_video" in dictionary and not self.video_recording:
                record_thread = Thread(target = self.RecordVideo)
                record_thread.daemon = True
                record_thread.start()
            self.SendShadow()
            self.SaveSettings()
        
        except Exception as e:
            print("Exception in subscriber: " + str(e))
        
    # Handles recieving the shadow callback
    def ShadowCallback(self, data, param2, param3):
        print(data)
        
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
                      "upload_video" : self.upload_video, "use_light" : self.use_light,
                      "enabled" : self.enabled}
        jsonStr = json.dumps(dictionary)

        return jsonStr
        
    # Records a video
    def RecordVideo(self):
        if self.video_recording:
            return
        self.video_recording = True
        try:
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
        except Exception as e:
            print("Exception in record video: " + str(e))
        if self.upload_video:
            try:
                print("Uploading video to Google Drive...")
                file_metadata = {'name': file_stamp + '.mp4'}
                media = MediaFileUpload(file_name + ".mp4", mimetype='video/mp4')
                file = self.service.files().create(body=file_metadata,
                                            media_body=media,
                                            fields='id').execute()
                print("Video uploaded!")
            except Exception as e:
                print("Video upload failed: " + str(e))
            
        self.videos_recorded_from_start += 1
        self.SendShadow()
        self.video_recording = False
        
    def motion_detect(self):
        imageFiles = []

        vs = VideoStream(src=0).start()
        time.sleep(2.0)

        nextRecordTime = 0.0
        occupiedTimeout = 0.0
        imageCount = 0
        # initialize the first frame in the video stream
        firstFrame = None
        occupied = False
        # loop over the frames of the video
        while True:
            # grab the current frame and initialize the occupied/unoccupied
            # text
            frame = vs.read()
            frame = frame
            text = "Unoccupied"
     
            # if the frame could not be grabbed, then we have reached the end
            # of the video
            if frame is None:
                break
     
            # resize the frame, convert it to grayscale, and blur it
            frame = imutils.resize(frame, width=500)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
     
            # if the first frame is None, initialize it
            if firstFrame is None:
                firstFrame = gray
                continue
            
            # compute the absolute difference between the current frame and
            # first frame
            frameDelta = cv2.absdiff(firstFrame, gray)
            thresh = cv2.threshold(frameDelta, move_threshold, 255, cv2.THRESH_BINARY)[1]
     
            # dilate the thresholded image to fill in holes, then find contours
            # on thresholded image
            thresh = cv2.dilate(thresh, None, iterations=2)
            cnts = cv2.findContours(thresh.copy(), cv2.RETR_TREE,
                cv2.CHAIN_APPROX_SIMPLE)
                
            cnts = cnts[1] #if imutils.is_cv2() else cnts[1]
            #print(cnts)
            #if cnts != None:
            # loop over the contours
            for c in cnts:
                # if the contour is too small, ignore it
                #if cv2.contourArea(c) < args["min_area"]:
                #	continue
                #print(cv2.contourArea(c))
                contour_area = cv2.contourArea(c)
                #for x in range(0, len(c)):
                #    contour_number += c[x]
                #try:
                #    val1 = cv2.contourArea(c)
                #    print("No exception")
                #except:
                #    pass
 
                # compute the bounding box for the contour, draw it on the frame,
                # and update the text
                if (contour_area > 300):
                    #print("Greater than zero")
                    (x, y, w, h) = cv2.boundingRect(c)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    text = "Occupied"
                    if (occupied == False):
                        print("Motion detect!")
                    occupied = True
                    timeNow = time.time()
            
                # draw the text and timestamp on the frame
            cv2.putText(frame, "Room Status: {}".format(text), (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            #cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
            #    (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
            #if (show_images == True):
                # show the frame and record if the user presses a key
            #    cv2.imshow("Security Feed", frame)
            #    cv2.imshow("Thresh", thresh)
            #    cv2.imshow("Frame Delta", frameDelta)
            timeNow = time.time()
            # Save frames of the intruder every so often and store them to the hard drive
            if (nextRecordTime < timeNow):
                nextRecordTime = timeNow + 1.0

            # Reset occupied every few seconds
            if (occupiedTimeout < timeNow):
                occupied = False
                firstFrame = None
                occupiedTimeout = timeNow + 10.0

            key = cv2.waitKey(1) & 0xFF
     
            # if the `q` key is pressed, break from the lop
            if key == ord("q"):
                break
     
        # cleanup the camera and close any open windows
        vs.stop()
        cv2.destroyAllWindows()

    # Handles motion getting detected
    def MotionDetected(self, pin):
        if self.video_recording or not self.enabled:
            return
        print("Motion detected: " + str(self.detections))
        self.detections += 1
        record_thread = Thread(target = self.RecordVideo)
        record_thread.daemon = True
        record_thread.start()
        
def StartFlask():
    try:
        app.run(host='0.0.0.0', port=80, debug=False)
        
    except Exception as e:
        print("Unable to start flask, restarting: " + str(e))
        time.sleep(1)
        StartFlask()
        
if __name__ == '__main__':
    pir = PIRCamera()
    
    #StartFlask()

    
    while (True):
        time.sleep(1)
