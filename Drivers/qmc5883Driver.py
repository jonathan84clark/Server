#!/usr/bin/python

import smbus
import time
import subprocess
# The default I2C address of this chip
QMC5883L_ADDR = 0x0D

# Register numbers
QMC5883L_X_LSB = 0
QMC5883L_X_MSB = 1
QMC5883L_Y_LSB = 2
QMC5883L_Y_MSB = 3
QMC5883L_Z_LSB = 4
QMC5883L_Z_MSB = 5
QMC5883L_STATUS = 6
QMC5883L_TEMP_LSB = 7
QMC5883L_TEMP_MSB = 8
QMC5883L_CONFIG = 9
QMC5883L_CONFIG2 = 10
QMC5883L_RESET = 11
QMC5883L_RESERVED = 12
QMC5883L_CHIP_ID = 13

# Bit values for the STATUS register
QMC5883L_STATUS_DRDY = 1
QMC5883L_STATUS_OVL = 2
QMC5883L_STATUS_DOR = 4

# Oversampling values for the CONFIG register
QMC5883L_CONFIG_OS512 = 0x00
QMC5883L_CONFIG_OS256 = 0x40
QMC5883L_CONFIG_OS128 = 0x80
QMC5883L_CONFIG_OS64 = 0xC0

# Range values for the CONFIG register */
QMC5883L_CONFIG_2GAUSS = 0x00
QMC5883L_CONFIG_8GAUSS = 0x10

# Rate values for the CONFIG register
QMC5883L_CONFIG_10HZ = 0x00
QMC5883L_CONFIG_50HZ = 0x04
QMC5883L_CONFIG_100HZ = 0x08
QMC5883L_CONFIG_200HZ = 0x0C

# Mode values for the CONFIG register */
QMC5883L_CONFIG_STANDBY = 0x00
QMC5883L_CONFIG_CONT = 0x01

# Apparently M_PI isn't available in all environments.
M_PI = 3.14159265358979323846264338327950288

bus = smbus.SMBus(1)    # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)

DEVICE_ADDRESS = 0x0D      #7 bit address (will be left shifted to add the read write bit)
DEVICE_REG_MODE1 = 0x00
DEVICE_REG_LEDOUT0 = 0x1d

addr = QMC5883L_ADDR
oversampling = QMC5883L_CONFIG_OS512
range = QMC5883L_CONFIG_2GAUSS
rate = QMC5883L_CONFIG_50HZ
mode = QMC5883L_CONFIG_CONT

def reconfig():
  bus.write_byte_data(addr,QMC5883L_CONFIG,oversampling|range|rate|mode)

def reset():
  bus.write_byte_data(addr,QMC5883L_RESET,0x01)
  reconfig()

def init():
  # This assumes the wire library has been initialized.
  addr = QMC5883L_ADDR
  oversampling = QMC5883L_CONFIG_OS512
  range = QMC5883L_CONFIG_2GAUSS
  rate = QMC5883L_CONFIG_50HZ
  mode = QMC5883L_CONFIG_CONT
  reset()

while (True):
    output = subprocess.check_output(['i2cdump', '-y', '-r', '0x00-0x0D', '1', '0x0D'])
    lines = output.splitlines()
    bytes = lines[1].split(' ')
    xBytes = '0x' + bytes[2] + bytes[1]
    yBytes = '0x' + bytes[2] + bytes[3]
    zBytes = '0x' + bytes[6] + bytes[5]
    tempBytes = '0x' + bytes[9] + bytes[8]

    xInt = int(xBytes, 16)
    yInt = int(yBytes, 16)
    zInt = int(zBytes, 16)
    temp = int(tempBytes, 16)
    print(xInt)
    print(yInt)
    print(zInt)
    print(temp)
    time.sleep(0.5)
