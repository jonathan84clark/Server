import socket
import time

UDP_IP = "192.168.1.5"
UDP_PORT = 11000
MESSAGE = "Hello, World!"

print "UDP target IP:", UDP_IP
print "UDP target port:", UDP_PORT
print "message:", MESSAGE


sock = socket.socket(socket.AF_INET, # Internet
                      socket.SOCK_DGRAM) # UDP

while (True):
    sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
    time.sleep(0.01)