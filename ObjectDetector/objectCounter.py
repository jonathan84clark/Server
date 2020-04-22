#######################################################################
# OBJECT COUNTER
# DESC: The object counter uses the Jetson Nano's tenser flow machine learning
# to detect objects entering it's view. This device is to be used as a 
# security/analyitics system. 
# See https://news.developer.nvidia.com/realtime-object-detection-in-10-lines-of-python-on-jetson-nano/
# Author: Jonathan L Clark
# Date: 4/21/2020
######################################################################
import datetime
import jetson.inference
import jetson.utils

image_counter = 0
image_path = '/home/jonathan/Pictures/'
net = jetson.inference.detectNet("ssd-mobilenet-v2", threshold=0.5)
camera = jetson.utils.gstCamera(640, 480, "/dev/video0")
#display = jetson.utils.glDisplay()
prev_objects = {}

#while display.IsOpen():
while True:
    img, width, height = camera.CaptureRGBA(zeroCopy=1)
    detections = net.Detect(img, width, height)
    detected_ids = {}
    newDetection = False
    #display.RenderOnce(img, width, height)

    # Determine detected objects for this frame
    for x in range(0, len(detections)):
        if detections[x].ClassID in detected_ids:
            detected_ids[detections[x].ClassID] += 1
        else:
            detected_ids[detections[x].ClassID] = 0

        
    for key in detected_ids:
        # Detect if a new object entered the field of view
        if not key in prev_objects or detected_ids[key] != prev_objects[key]:
            print("Object of type: " + str(key) + " entered view")
            newDetection = True
    
    prev_objects = {}
    for key in detected_ids:
        prev_objects[key] = detected_ids[key]

    if newDetection:
        date_stamp = datetime.datetime.now().strftime('%m_%d_%Y_%H_%M_%S')
        image_name = image_path + str(image_counter) + "_" + date_stamp + ".png"
        image_counter += 1
        jetson.utils.saveImageRGBA(image_name, img, width, height)
    #display.SetTitle("Object Detection | Network (:.0f) FPS".format(net.GetNetworkFPS()))
