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
serialPort = "/dev/ttyUSB0"
logDirectory = "/home/jonathan/Documents/weatherLog.csv"
csv_file = "/home/jonathan/Documents/weatherData.csv"
csv_columns = ['Date','Time','Outdoor Temp', 'Indoor Temp', 'Indoor Humid', 'IR Sensor']
delayBetweenCollect = 60

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
        file = open(logName, "a+")
    else:
        file = open(logName, "w")
        file.write("Date,Time,Module,Level,Message\n")
    file.write(csvString)
    file.close()
    print("[" + module + "] " + str(level) + ": " + message)

def pullData(lat, long):
    contents = urllib2.urlopen("https://api.weather.gov/points/" + str(lat) + "," + str(long)).read()
    jsonData = json.loads(contents)
    weatherData = urllib2.urlopen(jsonData["properties"]["forecast"]).read()
    jsonData = json.loads(weatherData)
    recentData = jsonData["properties"]["periods"][0]
	
    return recentData

# Gets the current external temperature and climate info from yahoo
def getClimateState():
    global dataSet
    port = serial.Serial(serialPort, 1)
    port.baudrate = 9600
    
    while (True):
        isFirst = True
        t = datetime.datetime.now()
        dataSet["Date"] = t.strftime("%m/%d/%y")
        dataSet["Time"] = t.strftime("%H:%M:%S")
        
        # Collect local outdoor weather data from Noaa
        try:
            data = pullData(47.689076, -117.284006)
            dataSet["Outdoor Temp"] = data["temperature"]
        except:
            write_log("OutdoorCollection", 1, "Unable to read data from Yahoo")
        
        # Collect local indoor weather from a serial temperature sensor 
        try:
            output = port.readline().strip()
            data = output.split(',')
            dataSet["Indoor Temp"] = data[0]
            dataSet["Indoor Humid"] = data[1]
            dataSet["IR Sensor"] = data[3]
            print(data[0])
        except:
            write_log("IndoorCollection", 1, "Unable to read data from serial port")
        
        # Save the local data to a CSV file
        try:
            f = open("/home/jonathan/Documents/weatherData.csv", "a+")
            line = ""
            for csvItem in csv_columns:
                if (isFirst == True):
                    line = line + str(dataSet[csvItem])
                    isFirst = False
                else:
                    line = line + ","+ str(dataSet[csvItem])
            line = line + "\n"
            f.write(line)
            f.close()
            print(line)
        except IOError:
            write_log("DataSave", 1, "Unable to write CSV data to file")
        time.sleep(delayBetweenCollect)
		
if __name__ == '__main__':
    getClimateState()
