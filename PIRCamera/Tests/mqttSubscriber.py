import time
import paho.mqtt.client as paho
#broker="broker.hivemq.com"
broker="192.168.1.14"
#define callback
def on_message(client, userdata, message):
    time.sleep(1)
    print("received message =",str(message.payload.decode("utf-8")))

client= paho.Client("client-001")
######Bind function to callback
client.on_message=on_message
#####
print("connecting to broker ",broker)
client.connect(broker)#connect
client.loop_start() #start loop to process received messages
print("subscribing ")
client.subscribe("house/bulb1")#subscribe

while True:
    time.sleep(1)

#time.sleep(2)
#print("publishing ")
#client.publish("house/bulb1","on")#publish
#time.sleep(4)
#client.disconnect() #disconnect
#client.loop_stop() #stop loop