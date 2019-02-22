#!/usr/bin/python
#################################################################
# THERMOSTAT
# DESC: The thermostat application is a multi-threaded python program
# designed to manage the temperature system of a house.
# The server must run on Python 2.7
# Modifier: Jonathan L Clark
# Date: 11/3/2018. Started fleshing out basic thermostat operating
# code.
# Update: 11/8/2018, Added the statistics measurement system as well
# as the other needed threads and sub systems. Validated that all systems
# are working.
# Update: 11/10/2018, The relay board uses LOW values to enable relays.
# On boot the GPIO pins are low which would turn on all relays. So 
# what we will do is have the 4th really switch the power. The power will
# only be applied if that relay is in the off position (high). This will
# allow us to control when the system is working.
# Update: 2/21/2019, Cleaned up the code. Also added the code for the new 
# Yahoo weather API.
##################################################################
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from weather import Weather, Unit
import SocketServer
import os
from os import curdir, sep
import time
from sys import argv
from threading import Thread
from time import sleep
import datetime
import json
import time, uuid, urllib, urllib2
import hmac, hashlib
from base64 import b64encode
import Adafruit_BMP.BMP280 as BMP280
import RPi.GPIO as GPIO

# Setup the GPIO pins
GPIO.setwarnings(False) # Disable unused warnings
GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme
GPIO.setup(27, GPIO.OUT) # Heater Pin
GPIO.setup(22, GPIO.OUT) # Fan Pin
GPIO.setup(23, GPIO.OUT) # AC Pin
GPIO.setup(24, GPIO.OUT) # Main power line

# Clear all relays
GPIO.output(27, GPIO.HIGH)
GPIO.output(22, GPIO.HIGH)
GPIO.output(23, GPIO.HIGH)
GPIO.output(24, GPIO.HIGH)

sensor = BMP280.BMP280()

location = 'spokane,wa'
variance = 1
app_id = ''
consumer_key = ''
consumer_secret = ''

logFilePath = "C:\\Users\\jonat\\Desktop\\"
#logFilePath = "/home/pi/GitHub/Server/Thermastat"
supported_files = {".html" : 'text/html', ".css" : 'text/css', "jpeg" : 'image/jpeg',
                   ".js" : 'text/javascript'}

dataSet = {"target" : 69.0, "temperature" : 60, "humidity" : 20, "weatherTemp": 70.0, "weatherHumid": 30.0, "windspd": 20,
           "acStatus" : False, "fanStatus" : False, "heaterStatus": False, "autoStatus": True}

class S(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
    
    def statusToString(self, status):
        if (status == True):
            return "On"
        else:
            return "Off"

    def do_GET(self):
        if (self.path == "/"):
            self.path = "/index.html"
        print(self.path)
        
        curdir = "/home/pi/GitHub/Server/Thermastat/"
        file_path = curdir + sep + self.path
        filename, file_extension = os.path.splitext(file_path)
        print(file_extension)
        if (self.path == "/data.js"):
            self.send_response(200)
            self.send_header('Content-type', "text/json")
            self.end_headers()
            jsonString = json.dumps(dataSet)
            self.wfile.write(jsonString)
        elif (os.path.isfile(file_path) and file_extension in supported_files):
            f = open(file_path, 'rb')
            self.send_response(200)
            self.send_header('Content-type', supported_files[file_extension])
            self.end_headers()
            self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.end_headers()

    def do_HEAD(self):
        self._set_headers()
    
    def clear_system(self):
        global dataSet
        dataSet["autoStatus"] = False
        dataSet["heaterStatus"] = False
        dataSet["acStatus"] = False
        dataSet["fanStatus"] = False
        GPIO.output(27, GPIO.HIGH)
        GPIO.output(22, GPIO.HIGH)
        GPIO.output(23, GPIO.HIGH)

    # Turns the AC on or off
    def toggle_ac(self):
        global dataSet
        self.clear_system()
        if (dataSet["acStatus"] == True):
            dataSet["acStatus"] = False
            GPIO.output(23, GPIO.HIGH)
            write_log("SERVER", 4, "AC turned off")
        else:
            dataSet["acStatus"] = True
            GPIO.output(23, GPIO.LOW)
            write_log("SERVER", 4, "AC turned on")
    
    # Turns the fan on or off
    def toggle_fan(self):
        global dataSet
        self.clear_system()
        if (dataSet["fanStatus"] == True):
            dataSet["fanStatus"] = False
            GPIO.output(22, GPIO.HIGH)
            write_log("SERVER", 4, "Fan turned off")
        else:
            dataSet["fanStatus"] = True
            GPIO.output(22, GPIO.LOW)
            write_log("SERVER", 4, "Fan turned on")

    # Turns the heat on or off
    def toggle_heat(self):
        global dataSet
        self.clear_system()
        if (dataSet["heaterStatus"] == True):
            dataSet["heaterStatus"] = False
            GPIO.output(27, GPIO.HIGH)
            write_log("SERVER", 4, "Heater turned off")
        else:
            dataSet["heaterStatus"] = True
            GPIO.output(27, GPIO.LOW)
            write_log("SERVER", 4, "Heater turned on")

    # Turns the heat on or off
    def toggle_auto(self):
        global dataSet
        self.clear_system()
        if (dataSet["autoStatus"] == True):
            dataSet["autoStatus"] = False
            write_log("SERVER", 4, "Auto mode off")
        else:
            dataSet["autoStatus"] = True
            write_log("SERVER", 4, "Auto mode on")

    # Turns the heat on or off
    def toggle_off(self):
        self.clear_system()
        dataSet["autoStatus"] = False
        pass

    def do_POST(self):
        global dataSet
        # Doesn't do anything with posted data
        output = "Submitted"
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        post_list = post_data.split("&") # Extract the individual post commands
        for post_str in post_list:
            key_value = post_str.split("=")
            if (len(key_value) == 2):
                if (key_value[0] == "off"):
                    self.toggle_off()
                elif (key_value[0] == "ac"):
                    self.toggle_ac()
                elif (key_value[0] == "fan"):
                    self.toggle_fan()
                elif (key_value[0] == "heat"):
                    self.toggle_heat()
                elif (key_value[0] == "auto"):
                    self.toggle_auto()
                elif (key_value[0] == "target"):
                    dataSet["target"] = float(key_value[1])
                    write_log("SERVER", 2, "Target temp set to: " + str(key_value[1]))
                else:
                    write_log("SERVER", 1, "ERROR: Invalid command: " + post_str)
            else:
                write_log("SERVER", 1, "ERROR: Invalid command format: " + post_str)
            
        self._set_headers()
        self.wfile.write("<html><body><h1>" + output + "</h1></body></html>")

def runServer(server_class=HTTPServer, handler_class=S, port=5000):
    global dataSet
    
    try:
        server_address = ('', port)
        httpd = server_class(server_address, handler_class)
        print 'Starting httpd...'
        httpd.serve_forever()
    except:
       write_log("SERVER", 1, "ERROR: Unable to start server, trying again")
       sleep(5)
       runServer()
        
def getTemperature():
    global sensor
    global dataSet

    tempC = sensor.read_temperature()
    dataSet["temperature"] = (tempC * 9.0 / 5.0) + 32.0

    return dataSet["temperature"]

# Write to the system log file
def write_log(module, level, message):
    appDir = logFilePath
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

# Write to the system log file
def log_climate_stats():
    global dataSet
    appDir = logFilePath
    appDir += "/Logs/"
    if os.path.exists(appDir) == False:
       os.mkdir(appDir)
    t = datetime.datetime.now()
    logName = appDir + t.strftime("Log_Stats" + "%d_%m_%y_.csv")
    dateString = t.strftime("%d/%m/%y")
    timeString = t.strftime("%H:%M:%S")
    csvString = dateString + "," + timeString + "," + str(dataSet["weatherTemp"]) + "," + str(dataSet["temperature"]) + "," + str(dataSet["windspd"]) + ","
    csvString += str(dataSet["weatherTemp"]) + "," + str(dataSet["weatherHumid"]) + "," + str(dataSet["humidity"]) + "\n"
    if os.path.exists(logName):
        file = open(logName, "a")
    else:
        file = open(logName, "w")
        file.write("Date,Time,Outside Temp,Inside Temp,Outside Wind Speed,Outside Wind Direction, Outside Humidity, Inside Humidity\n")
    file.write(csvString)
    file.close()

# Gets the current external temperature and climate info from yahoo
def getClimateState(request):
    global dataSet
    try:
        #write_log("THERMOSTAT", 4, "Pulling real-world weather")
        response = urllib2.urlopen(request).read()
        loaded_json = json.loads(response)
        dataSet["weatherHumid"] = loaded_json["current_observation"]["atmosphere"]["humidity"]
        dataSet["weatherTemp"] = loaded_json["current_observation"]["condition"]["temperature"]
        #dataSet["windspd"] = location.wind.speed
        #dataSet["windDir"] = location.wind.directio
    except:
        write_log("THERMOSTAT", 1, "EXCEPTION: Unable to pull real-world weather")

    if (int(dataSet["weatherTemp"]) < 60.0): # Colder temperatures are below 60 degrees
        return 1
    else:
        return 0

# Runs the automatic thermostat thread
def runThermostat():
    global dataSet
    global sensor
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
    
    while (True):
        curClimate = getClimateState(request)
        cur_temp = getTemperature()
        # Temperature is out of range, now lets turn things on
        # In cold temps ONLY use the heat, climate will be pulled from special RTC function
        if (dataSet["autoStatus"] == True): # We only execute the thermostat code if we are in auto-mode
            if (curClimate == 1):
                if (cur_temp < (dataSet["target"] - variance) and dataSet["heaterStatus"] == False):
                    dataSet["heaterStatus"] = True
                    write_log("THERMOSTAT", 4, "Turning on heater")
                    GPIO.output(27, GPIO.LOW)
                elif (cur_temp >= (dataSet["target"] + variance) and dataSet["heaterStatus"] == True):
                    dataSet["heaterStatus"] = False
                    write_log("THERMOSTAT", 4, "Turning off heater")
                    GPIO.output(27, GPIO.HIGH)
            else:
                if (cur_temp > (dataSet["target"] + variance) and dataSet["acStatus"] == False):
                    dataSet["acStatus"] = True
                    write_log("THERMOSTAT", 4, "Turning on ac")
                    GPIO.output(23, GPIO.LOW)
                elif (cur_temp <= (dataSet["target"] - variance) and dataSet["acStatus"] == True):
                    dataSet["acStatus"] = False
                    write_log("THERMOSTAT", 4, "Turning off ac")
                    GPIO.output(23, GPIO.HIGH)
        sleep(15) # We are in no hurry, only check data every 15 seconds
     
# Run Stats logger; the stats logger tracks the temperature, humidity and other stats over time           
def runStatsLogger():
    global dataSet
    global sensor

    while (True):
        log_climate_stats()
        sleep(21600) # Log data every 6 hours
        

if __name__ == "__main__":
    #sleep(50)
    write_log("MAIN", 1, "System Started")

	# Start up the server thread
    thread = Thread(target = runServer)
    thread.daemon = True
    thread.start()

    # Start the thermostat thread
    thermostatThread = Thread(target = runThermostat)
    thermostatThread.daemon = True
    thermostatThread.start()
    
    # Start the statistics monitoring system
    statsThread = Thread(target = runStatsLogger)
    statsThread.daemon = True
    statsThread.start()
    print("All threads started")
    while (True):
        pass
        
