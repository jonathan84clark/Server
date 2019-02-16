#################################################################
# Motion Detector
# DESC: Application operates a standard USB video device and runs it as
# a motion activated security camera. 
# Original code as pulled from online and modified
# Date: 11/22/2018: Added code to capture frames every second when
# motion is sensed.
# Update: 12/6/2018, Added code to support uploading files to Google Drive
# now images are added to Google drive when they are captured.
# Update: 12/7/2018, Added code to enable Google Drive upload multi-threading
# Update: 2/15/2019, Fixed an issue where a null frame would sometimes occur on
# start. Added a check for this frame. Also added support for Gmail messages/notifications.
#################################################################
from __future__ import print_function
from imutils.video import VideoStream
import argparse
import datetime
import imutils
import time
import cv2
import os
import threading
import pickle
import os.path
import base64
from urllib2 import HTTPError
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from email.mime.text import MIMEText

move_threshold = 50
show_images = True
imageDirectory = "C:\\Users\\jonat\\Desktop\\"
logDirectory = "C:\\Users\\jonat\\Desktop\\"
# If modifying these scopes, delete the file token.json.
#SCOPES = 'https://www.googleapis.com/auth/drive.metadata.readonly'
SCOPES = 'https://www.googleapis.com/auth/drive'
# If modifying these scopes, delete the file token.pickle.
SCOPES_GMAIL = ['https://mail.google.com/']

# Write to the log file
def write_log(module, level, message):
    appDir = logDirectory
    appDir += "/Logs/"
    if os.path.exists(appDir) == False:
       os.mkdir(appDir)
    t = datetime.datetime.now()
    logName = appDir + t.strftime("Log_" + "%d_%m_%y_.csv")
    dateString = t.strftime("%d/%m/%y")
    timeString = t.strftime("%H:%M:%S")
    csvString = dateString + "," + timeString + "," + module + "," + str(level) + "," + message + "\n"
    if os.path.exists(logName):
        file = open(logName, "a")
    else:
        file = open(logName, "w")
        file.write("Date,Time,Module,Level,Message\n")
    file.write(csvString)
    file.close()
    print("[" + module + "] " + str(level) + ": " + message)
   

def motion_detect():
	imageFiles = []
	gauth = GoogleAuth()
	# Try to load saved client credentials
	gauth.LoadCredentialsFile("mycreds.txt")
	if gauth.credentials is None:
		# Authenticate if they're not there
		gauth.LocalWebserverAuth()
	elif gauth.access_token_expired:
		# Refresh them if expired
		gauth.Refresh()
	else:
		# Initialize the saved creds
		gauth.Authorize()
	# Save the current credentials to a file
	gauth.SaveCredentialsFile("mycreds.txt")

	drive = GoogleDrive(gauth)

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
		cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
			cv2.CHAIN_APPROX_SIMPLE)
		cnts = cnts[0] #if imutils.is_cv2() else cnts[1]
        
		if cnts != None:
		# loop over the contours
			for c in cnts:
				# if the contour is too small, ignore it
				#if cv2.contourArea(c) < args["min_area"]:
				#	continue
 
				# compute the bounding box for the contour, draw it on the frame,
				# and update the text
				(x, y, w, h) = cv2.boundingRect(c)
				cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
				text = "Occupied"
				if (occupied == False):
					write_log("SEC_CAM", 1, "Motion event detected")
				occupied = True
				timeNow = time.time()
		
			# draw the text and timestamp on the frame
		cv2.putText(frame, "Room Status: {}".format(text), (10, 20),
			cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
		cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
			(10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
		if (show_images == True):
			# show the frame and record if the user presses a key
			cv2.imshow("Security Feed", frame)
			cv2.imshow("Thresh", thresh)
			cv2.imshow("Frame Delta", frameDelta)
		timeNow = time.time()
		# Save frames of the intruder every so often and store them to the hard drive
		if (nextRecordTime < timeNow):
			if (occupied == True):
				now = datetime.datetime.now()
				nowStr = now.strftime("%m_%d_%y_%H_%M_%S")
				imageName =  imageDirectory + "img" + str(imageCount) + ".jpg"
				imageCount = imageCount + 1
				cv2.imwrite(imageName, frame)
				imageFiles.append(imageName)
			nextRecordTime = timeNow + 1.0

		# Reset occupied every few seconds
		if (occupiedTimeout < timeNow):
			occupied = False
			firstFrame = None
			processThread = threading.Thread(target=uploadImages, args=(drive,imageFiles))  # <- note extra ','
			processThread.start()
			imageFiles = []
			occupiedTimeout = timeNow + 10.0

		key = cv2.waitKey(1) & 0xFF
 
		# if the `q` key is pressed, break from the lop
		if key == ord("q"):
			break
 
	# cleanup the camera and close any open windows
	vs.stop()
	cv2.destroyAllWindows()

def uploadImages(drive, imageFiles):
	for imageFile in imageFiles:
		uploadToDrive(drive, imageFile)

def uploadToDrive(drive, filePath):
    pass
	#textfile = drive.CreateFile()
	#textfile.SetContentFile(filePath)
	#textfile.Upload()

def send_email(sender, to, subject, message_text):
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES_GMAIL)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)

    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    message = {'raw': base64.urlsafe_b64encode(message.as_string())}
    #try:
    message = (service.users().messages().send(userId="jonathan84clark@gmail.com", body=message)
               .execute())
        #print 'Message Id: %s' % message['id']
    return message
    #except HttpError, error:
    #    pass
        #print 'An error occurred: %s' % error 

def main():
    #motion_detect()
	send_email("jonathan84clark@gmail.com", "jonathan84clark@gmail.com", "Motion Event", "Motion Event")

if __name__ == '__main__':
    main()
#motion_detect()