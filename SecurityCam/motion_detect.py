#################################################################
# Motion Detector
# DESC: Application operates a standard USB video device and runs it as
# a motion activated security camera. 
# Original code as pulled from online and modified
# Date: 11/22/2018: Added code to capture frames every second when
# motion is sensed.
#################################################################
from imutils.video import VideoStream
import argparse
import datetime
import imutils
import time
import cv2

imageDirectory = "C:\\Users\\jonat\\Desktop\\"
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
	thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]
 
	# dilate the thresholded image to fill in holes, then find contours
	# on thresholded image
	thresh = cv2.dilate(thresh, None, iterations=2)
	cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
		cv2.CHAIN_APPROX_SIMPLE)
	cnts = cnts[0] if imutils.is_cv2() else cnts[1]
 
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
		occupied = True
		timeNow = time.time()
		
			# draw the text and timestamp on the frame
	cv2.putText(frame, "Room Status: {}".format(text), (10, 20),
		cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
	cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
		(10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
 
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
vs.stop()# if args.get("video", None) is None else vs.release()
cv2.destroyAllWindows()