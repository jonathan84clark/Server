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
# what we will do is have the 4th realy switch the power. The power will
# only be applied if that relay is in the off position (high). This will
# allow us to control when the system is working.
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
target_temp = 69
system_enabled = True
ac_on = False
heat_on = False
fan_on = False
variance = 1
auto_mode = True

# Current statistics
insideTemp = 60
insideHumid = 20
outsideTemp = 70
outsideHumid = 30
outsideWindSpd = 20
outsideWindDir = 270

supported_files = {".html" : 'text/html', ".css" : 'text/css', "jpeg" : 'image/jpeg',
                   ".js" : 'text/javascript'}

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
            jsonString = '{"target":' + str(target_temp) + ', "temperature":' + str(insideTemp) + ', "humidity":' + str(insideHumid) + ', '
            jsonString += '"weatherTemp":' + str(outsideTemp) + ', "weatherHumid":' + str(outsideHumid) + ', "windSpd":' + str(outsideWindSpd) + ', '
            jsonString += '"acStatus":"' + self.statusToString(ac_on) + '", "fanStatus":"' + self.statusToString(fan_on) + '", '
            jsonString += '"heaterStatus":"' + self.statusToString(heat_on) + '", "autoStatus":"' + self.statusToString(auto_mode) + '"}'
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
        global auto_mode
        global heat_on
        global ac_on
        global fan_on
        auto_mode = False
        heat_on = False
        ac_on = False
        fan_on = False
        GPIO.output(27, GPIO.HIGH)
        GPIO.output(22, GPIO.HIGH)
        GPIO.output(23, GPIO.HIGH)

    # Turns the AC on or off
    def toggle_ac(self):
        global ac_on
        self.clear_system()
        if (ac_on == True):
            ac_on = False
            GPIO.output(23, GPIO.HIGH)
            write_log("SERVER", 4, "AC turned off")
        else:
            ac_on = True
            GPIO.output(23, GPIO.LOW)
            write_log("SERVER", 4, "AC turned on")
    
    # Turns the fan on or off
    def toggle_fan(self):
        global fan_on
        self.clear_system()
        if (fan_on == True):
            fan_on = False
            GPIO.output(22, GPIO.HIGH)
            write_log("SERVER", 4, "Fan turned off")
        else:
            fan_on = True
            GPIO.output(22, GPIO.LOW)
            write_log("SERVER", 4, "Fan turned on")

    # Turns the heat on or off
    def toggle_heat(self):
        global heat_on
        self.clear_system()
        if (heat_on == True):
            heat_on = False
            GPIO.output(27, GPIO.HIGH)
            write_log("SERVER", 4, "Heater turned off")
        else:
            heat_on = True
            GPIO.output(27, GPIO.LOW)
            write_log("SERVER", 4, "Heater turned on")

    # Turns the heat on or off
    def toggle_auto(self):
        global auto_mode
        self.clear_system()
        if (auto_mode == True):
            auto_mode = False
            write_log("SERVER", 4, "Auto mode off")
        else:
            auto_mode = True
            write_log("SERVER", 4, "Auto mode on")

    # Turns the heat on or off
    def toggle_off(self):
        self.clear_system()
        auto_mode = False
        pass

    def do_POST(self):
        global target_temp
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
                    target_temp = float(key_value[1])
                    write_log("SERVER", 2, "Target temp set to: " + str(key_value[1]))
                else:
                    write_log("SERVER", 1, "ERROR: Invalid command: " + post_str)
            else:
                write_log("SERVER", 1, "ERROR: Invalid command format: " + post_str)
            
        self._set_headers()
        self.wfile.write("<html><body><h1>" + output + "</h1></body></html>")

def runServer(server_class=HTTPServer, handler_class=S, port=5000):
    global target_temp
    global system_enabled
    global ac_on
    global heat_on
    global fan_on
    global variance
    global auto_mode
    global outsideTemp
    global outsideHumid
    global outsideWindSpd
    global outsideWindDir
    global insideTemp
    global insideHumid
    
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
    global insideTemp

    tempC = sensor.read_temperature()
    insideTemp = (tempC * 9.0 / 5.0) + 32.0

    return insideTemp

# Write to the system log file
def write_log(module, level, message):
    appDir = "/home/pi/GitHub/Server/Thermastat"#os.path.dirname(os.path.realpath(__file__))
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
    global target_temp
    global system_enabled
    global ac_on
    global heat_on
    global fan_on
    global variance
    global auto_mode
    global outsideTemp
    global outsideHumid
    global outsideWindSpd
    global outsideWindDir
    global insideTemp
    global insideHumid
    appDir = "/home/pi/GitHub/Server/Thermastat"#os.path.dirname(os.path.realpath(__file__))
    appDir += "/Logs/"
    if os.path.exists(appDir) == False:
       os.mkdir(appDir)
    t = datetime.datetime.now()
    logName = appDir + t.strftime("Log_Stats" + "%d_%m_%y_.csv")
    dateString = t.strftime("%d/%m/%y")
    timeString = t.strftime("%H:%M:%S")
    csvString = dateString + "," + timeString + "," + str(outsideTemp) + "," + str(insideTemp) + "," + str(outsideWindSpd) + ","
    csvString += str(outsideWindDir) + "," + str(outsideHumid) + "," + str(insideHumid) + "\n"
    if os.path.exists(logName):
        file = open(logName, "a")
    else:
        file = open(logName, "w")
        file.write("Date,Time,Outside Temp,Inside Temp,Outside Wind Speed,Outside Wind Direction, Outside Humidity, Inside Humidity\n")
    file.write(csvString)
    file.close()

# Gets the current external temperature and climate info from yahoo
def getClimateState():
    global target_temp
    global system_enabled
    global ac_on
    global heat_on
    global fan_on
    global variance
    global auto_mode
    global outsideTemp
    global outsideHumid
    global outsideWindSpd
    global outsideWindDir
    global insideTemp
    global insideHumid
    try:
        #write_log("THERMOSTAT", 4, "Pulling real-world weather")
        weather = Weather(Unit.FAHRENHEIT)
        location = weather.lookup_by_location('spokane')
        condition = location.condition
    
        outsideTemp = condition.temp
        outsideHumid = location.atmosphere.humidity
        outsideWindSpd = location.wind.speed
        outsideWindDir = location.wind.direction
    except:
        write_log("THERMOSTAT", 1, "EXCEPTION: Unable to pull real-world weather")

    if (int(outsideTemp) < 60.0): # Colder temperatures are below 60 degrees
        return 1
    else:
        return 0

# Runs the automatic thermostat thread
def runThermostat():
    global target_temp
    global system_enabled
    global ac_on
    global heat_on
    global fan_on
    global variance
    global auto_mode
    global outsideTemp
    global outsideHumid
    global outsideWindSpd
    global outsideWindDir
    global insideTemp
    global insideHumid
    global sensor
    
    while (True):
        curClimate = getClimateState()
        cur_temp = getTemperature()
        # Temperature is out of range, now lets turn things on
        # In cold temps ONLY use the heat, climate will be pulled from special RTC function
        if (auto_mode == True): # We only execute the thermostat code if we are in auto-mode
            if (curClimate == 1):
                if (cur_temp < (target_temp - variance) and heat_on == False):
                    heat_on = True
                    write_log("THERMOSTAT", 4, "Turning on heater")
                    GPIO.output(27, GPIO.LOW)
                elif (cur_temp >= (target_temp + variance) and heat_on == True):
                    heat_off = False
                    write_log("THERMOSTAT", 4, "Turning off heater")
                    GPIO.output(27, GPIO.HIGH)
            else:
                if (cur_temp > (target_temp + variance) and ac_on == False):
                    ac_on = True
                    write_log("THERMOSTAT", 4, "Turning on ac")
                    GPIO.output(23, GPIO.LOW)
                elif (cur_temp <= (target_temp - variance) and ac_on == True):
                    ac_on = False
                    write_log("THERMOSTAT", 4, "Turning off ac")
                    GPIO.output(23, GPIO.HIGH)
        sleep(15) # We are in no hurry, only check data every 15 seconds
     
# Run Stats logger; the stats logger tracks the temperature, humidity and other stats over time           
def runStatsLogger():
    global target_temp
    global system_enabled
    global ac_on
    global heat_on
    global fan_on
    global variance
    global auto_mode
    global outsideTemp
    global outsideHumid
    global outsideWindSpd
    global outsideWindDir
    global insideTemp
    global insideHumid
    global sensor

    while (True):
        log_climate_stats()
        sleep(21600) # Log data every 6 hours
        

if __name__ == "__main__":
    sleep(50)
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
        
