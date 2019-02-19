'''
Weather Logger
DESC: Collects outdoor weather data from Yahoo weather and
data from a serial weather sensor and logs the data to a CSV file.
The serial data logger is an Arduino Nano connected to a I2C temp/humidity
sensor. It is simply reading data from that device and serial.println the data
in CSV format.

Author: Jonathan L Clark
Date: 2/18/2019
'''

import os
import csv
import serial
import datetime
import time
from weather import Weather, Unit
import json
import time, uuid, urllib, urllib2
import hmac, hashlib
from base64 import b64encode

dataSet = {}

# Configuration settings
location = 'spokane,wa'
serialPort = "COM5"
logDirectory = "C:\\Users\\jonat\\Desktop\\"
csv_file = "C:\\Users\\jonat\\Desktop\\output.csv"
csv_columns = ['Date','Time','Outdoor Temp', 'Indoor Temp', 'Outdoor Humid', 'Indoor Humid', 'IR Sensor']
delayBetweenCollect = 5

app_id = ''
consumer_key = ''
consumer_secret = ''
		
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

# Gets the current external temperature and climate info from yahoo
def getClimateState():
    global dataSet
    port = serial.Serial(serialPort, 1)
    port.baudrate = 9600
    url = 'https://weather-ydn-yql.media.yahoo.com/forecastrss'
    method = 'GET'
    concat = '&'
    query = {'location': location, 'format': 'json'}
    oauth = {
            'oauth_consumer_key': consumer_key,
            'oauth_nonce': uuid.uuid4().hex,
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': str(int(time.time())),
            'oauth_version': '1.0'
    }

    merged_params = query.copy()
    merged_params.update(oauth)
    sorted_params = [k + '=' + urllib.quote(merged_params[k], safe='') for k in sorted(merged_params.keys())]
    signature_base_str =  method + concat + urllib.quote(url, safe='') + concat + urllib.quote(concat.join(sorted_params), safe='')

    composite_key = urllib.quote(consumer_secret, safe='') + concat
    oauth_signature = b64encode(hmac.new(composite_key, signature_base_str, hashlib.sha1).digest())

    oauth['oauth_signature'] = oauth_signature
    auth_header = 'OAuth ' + ', '.join(['{}="{}"'.format(k,v) for k,v in oauth.iteritems()])


    url = url + '?' + urllib.urlencode(query)
    request = urllib2.Request(url)
    request.add_header('Authorization', auth_header)
    request.add_header('Yahoo-App-Id', app_id)
    headerWritten = False
    while (True):
        t = datetime.datetime.now()
        dataSet["Date"] = t.strftime("%m/%d/%y")
        dataSet["Time"] = t.strftime("%H:%M:%S")
        
        # Collect local outdoor weather data from Yahoo
        try:
            response = urllib2.urlopen(request).read()
            loaded_json = json.loads(response)
            #for x in loaded_json:
            #	print(x)
            #	print(loaded_json[x])
            #	print("\n\n\n")
	    
            dataSet["Outdoor Humid"] = loaded_json["current_observation"]["atmosphere"]["humidity"]
            dataSet["Outdoor Temp"] = loaded_json["current_observation"]["condition"]["temperature"]
        except:
            write_log("OutdoorCollection", 1, "Unable to read data from Yahoo")
        
        # Collect local indoor weather from a serial temperature sensor 
        try:
            output = port.readline().strip()
            data = output.split(',')
            dataSet["Indoor Temp"] = data[0]
            dataSet["Indoor Humid"] = data[1]
            dataSet["IR Sensor"] = data[3]
        except:
            write_log("IndoorCollection", 1, "Unable to read data from serial port")
        
        # Save the local data to a CSV file
        try:
            f = open("C:\\Users\\jonat\\Desktop\\outputFile.csv", "a+")
            line = ""
            isFirst = True
            for headerItem in dataSet:
                if (isFirst == True):
                    line = line + str(dataSet[headerItem])
                    isFirst = False
                else:
                    line = line + ","+ str(dataSet[headerItem])
            line = line + "\n"
            f.write(line)
            f.close()
        except IOError:
            write_log("DataSave", 1, "Unable to write CSV data to file")
        #print(dataSet)
        time.sleep(delayBetweenCollect)
		
if __name__ == '__main__':
    getClimateState()
