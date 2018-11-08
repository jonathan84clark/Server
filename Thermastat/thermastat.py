#################################################################
# THERMOSTAT
# DESC: The thermostat application is a multi-threaded python program
# designed to manage the temperature system of a house.
# The server must run on Python 2.7
# Modifier: Jonathan L Clark
# Date: 11/3/2018. Started fleshing out basic thermostat operating
# code.
##################################################################
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer
import os
from os import curdir, sep
import time
from sys import argv
from threading import Thread
from time import sleep

target_temp = 69
system_enabled = True
ac_on = False
heat_on = False
fan_on = False
variance = 1
auto_mode = True

supported_files = {".html" : 'text/html', ".css" : 'text/css', "jpeg" : 'image/jpeg',
                   ".js" : 'text/javascript'}

class S(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        if (self.path == "/"):
            self.path = "/index.html"
        print(self.path)
        
        file_path = curdir + sep + self.path
        filename, file_extension = os.path.splitext(file_path)
        print(file_extension)
        if (self.path == "/data.js"):
            self.send_response(200)
            self.send_header('Content-type', "text/json")
            self.end_headers()
            self.wfile.write('{"target":78, "temperature":84, "humidity":32, "weatherTemp":32, "weatherHumid":43, "windSpd":15, "acStatus":"On", "fanStatus":"Off", "heaterStatus":"Off"}')
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
        
    def do_POST(self):
        # Doesn't do anything with posted data
        output = "Submitted"
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        post_list = post_data.split("&") # Extract the individual post commands
        for post_str in post_list:
            key_value = post_str.split("=")
            print(post_str)
            # TODO: split up the post strings of the format what=param&what2=param2
            # then send the proper commands to the thermostat thread
            
        self._set_headers()
        self.wfile.write("<html><body><h1>" + output + "</h1></body></html>")

def runServer(server_class=HTTPServer, handler_class=S, port=80):
    global target_temp
    global system_enabled

    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print 'Starting httpd...'
    httpd.serve_forever()

def getTemperature():
    return 49

def getClimateState():
    # TODO: Pull real world temperature data
    # If real world data is not available, extrapolate the temperature state from the month in the year
    outside_temp = 49
    if (outside_temp < 60): # Colder temperatures are below 60 degrees
        return "cold"
    else:
        return "warm"

def runThermostat():
    global target_temp
    global system_enabled
    global ac_on
    global heat_on
    global fan_on
    global variance
    global auto_mode
    
    while (True):
        curClimate = getClimateState()
        cur_temp = getTemperature()
        # Temperature is out of range, now lets turn things on
        # In cold temps ONLY use the heat, climate will be pulled from special RTC function
        if (auto_mode == True): # We only execute the thermostat code if we are in auto-mode
            if (curClimate == "cold"):
                if (cur_temp < (target_temp - variance) and heat_on == False):
                    heat_on = True
                    print("Turning on heater")
                    # TODO: Turn on the heater
                elif (cur_temp == (target_temp + variance) and heat_on == False):
                    heat_off = False
                    print("Turning the heater off")
                    # TODO: Turn the heater off
            else:
                if (cur_temp > (target_temp + variance) and ac_on == False):
                    ac_on = True
                    print("Turning on ac")
                    # TODO: Turn on the AC
                elif (cur_temp == (target_temp - variance) and ac_on == True):
                    ac_on = False
                    print("Turning off the ac")
        sleep(15) # We are in no hurry, only check data every 15 seconds
                


if __name__ == "__main__":
	# Start up the server thread
    thread = Thread(target = runServer)
    thread.start()

    thermostatThread = Thread(target = runThermostat)
    thermostatThread.start()
    print("All threads started")
    while (True):
        pass
