#!/bin/bash

# Shut off all relays pronto!

sudo echo "24" > /sys/class/gpio/export
sudo echo "22" > /sys/class/gpio/export
sudo echo "23" > /sys/class/gpio/export
sudo echo "27" > /sys/class/gpio/export

sudo echo "out" > /sys/class/gpio/gpio24/direction
sudo echo "out" > /sys/class/gpio/gpio22/direction
sudo echo "out" > /sys/class/gpio/gpio23/direction
sudo echo "out" > /sys/class/gpio/gpio27/direction

sudo echo "1" > /sys/class/gpio/gpio24/value
sudo echo "1" > /sys/class/gpio/gpio22/value
sudo echo "1" > /sys/class/gpio/gpio23/value
sudo echo "1" > /sys/class/gpio/gpio27/value



sleep 70
echo "Starting thermastat..."
python /home/pi/GitHub/Server/Thermastat/thermastat.py
