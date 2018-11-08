#!/usr/bin/python
# SystemInfo
# Description: This is a simple perl script that returns
# basic information about the current server in a jason format.
# It only works on Linux based OS.
# Author: Jonathan L Clark
# Date: 7/10/2018

import subprocess

print "Content-Type: text/html\n\n"
cpuInfo = subprocess.Popen(['cat', '/proc/cpuinfo'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
stdout,stderr = cpuInfo.communicate()

jasonStrArray = []
jsonString = "{"
lines = stdout.split('\n')
for line in lines:
   jsonElement = ""
   data = line.split(':')
   if "processor" in data[0]:
      jsonString += '""' + ":" + '""'"}"
      jasonStrArray.append(jsonString)
      jsonString = "{"
      pass
      #jsonString += "}"
      #jasonStrArray.append(jsonString)
      #jsonString = "{"
   if len(data) > 1 and len(data[0]) > 1:
      jsonElement = '"' + data[0].strip() + '"' + ":" + '"' + data[1].strip() + '",' 
      jsonString += jsonElement

jsonString = "}"
jasonStrArray.append(jsonString)
print jasonStrArray[1]


