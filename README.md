# Server
The Server is a series of small applications designed to perform useful functions for my family. The Server consists of a number of different tools written in different languages.

## Emailer
The emailer is an automated script that uses a Python script and a Google Email to send email. As the code stands today it uses a Web Camera to capture a picture and send that via email every few minutes. This acts as a security/monitoring system. This system is intended to be replaced by a full openCV motion detection solution later on.  

## Security Cam
The security cam software provides a number of useful tools. One application is to uses ffmpeg for live video streaming. This is intended to be used on a Raspberry Pi driven robot. Recently I have developed a new security camera application using open CV. Using a basic Web Camera open CV uses motion detection to "watch" a specific area. If motion is detected then frames are captured. In the future it is intended that these frames will be uploaded to Google Drive making it impossible for a thief to compromise the them before they are sent to the authorities.

## Server Pages
The server pages contain a basic Web Interface for the Server. Currently there are just a few useful things to run on a server in this way since SSH is can be used as a far more comprehensive interface.

## Thermostat
The Thermostat is a full-stack application designed to act as an Iot heater/ac control system. The thermostat backend code is written in Python and is designed to run on a Raspberry PI with an I2C temperature sensor attached. The front-end UI is a Web interface that allows users to login and change the temperature threshold. Weather data is pulled from Yahoo to determine if heating or cooling should be used.
