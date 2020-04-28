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
import time

# Some items we may wish to ignore
exclusion_list = [38, 37]

image_counter = 0
image_path = '/home/jonathan/Pictures/'
net = jetson.inference.detectNet("ssd-mobilenet-v2", threshold=0.80)
camera = jetson.utils.gstCamera(640, 480, "/dev/video0")
#display = jetson.utils.glDisplay()
prev_objects = {}
date_str = datetime.datetime.now().strftime('%m_%d_%Y_%H_%M_%S')
filename = '/home/jonathan/Documents/' + 'object_log_' + date_str + '.csv'
f = open(filename, "a")
f.write("Date,Time,Type,Instance ID,Confidence")
f.close()
print('Saving log data to: ' + filename)

#while display.IsOpen():
while True:
    img, width, height = camera.CaptureRGBA(zeroCopy=1)
    detections = net.Detect(img, width, height)
    detected_ids = {}
    newDetection = False
    #display.RenderOnce(img, width, height)

    # Determine detected objects for this frame
    for x in range(0, len(detections)):
        if not detections[x].ClassID in exclusion_list:
            if detections[x].ClassID in detected_ids:
                detected_ids[detections[x].ClassID].append({"instance" : detections[x].Instance, "confidence" : detections[x].Confidence})
                print("Instance id: " + str(detections[x].Instance))
            else:
                detected_ids[detections[x].ClassID] = []
                detected_ids[detections[x].ClassID].append({"instance" : detections[x].Instance, "confidence" : detections[x].Confidence})
                print("Instance id: " + str(detections[x].Instance))

        
    for key in detected_ids:
        # Detect if a new object entered the field of view
        if not key in prev_objects or len(detected_ids[key]) != len(prev_objects[key]):
            # find the largest instance id
            largest_id = 0
            newObject = detected_ids[key][0]
            for x in range(0, len(detected_ids[key])):
                if detected_ids[key][x]["instance"] > largest_id:
                    largest_id = detected_ids[key][x]["instance"]
                    newObject = detected_ids[key][x]
            csv_date_time = datetime.datetime.now().strftime('%m/%d/%Y,%H:%M:%S')
            csv_date_time += "," + str(key) + "," + str(newObject["instance"]) + "," + str(newObject["confidence"]) + "\n"
            f = open(filename, "a")
            f.write(csv_date_time)
            f.close()
            print("Object of type: " + str(key) + " entered view")
            newDetection = True
    
    prev_objects = {}
    for key in detected_ids:
        prev_objects[key] = detected_ids[key]

    if newDetection:
        date_stamp = datetime.datetime.now().strftime('%m_%d_%Y_%H_%M_%S')
        image_name = image_path + date_stamp + "_" + str(image_counter) + ".png"
        image_counter += 1
        jetson.utils.saveImageRGBA(image_name, img, width, height)
        time.sleep(0.2) # Wait 200ms to prevent chop in the same frame
    #display.SetTitle("Object Detection | Network (:.0f) FPS".format(net.GetNetworkFPS()))
