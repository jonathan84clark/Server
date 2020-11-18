import time
import paho.mqtt.client as paho
#broker="broker.hivemq.com"
broker="192.168.1.14"

client= paho.Client("client-002")
######Bind function to callback
#####
print("connecting to broker ",broker)
client.connect(broker)#connect

#print("publishing ")
client.publish("house/bulb1","on")#publish
#time.sleep(4)
client.disconnect() #disconnect
client.loop_stop() #stop loop