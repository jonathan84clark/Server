#############################################################
# AUTO EMAILER
# DESC: The auto emailer is a application that sends an email
# periodically for a certain number of days or months. It is 
# designed as a deterant to spammers. If someone continues
# to send spam emails after an unsubscibe request is sent
# this tool can be used to spam the spammers until they stop
# Author: Jonathan L Clark
# Date: 7/20/2018
#############################################################
import sys
import time
import datetime
import cv2
import numpy as np
import os
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import encoders

# Write to the log file
def write_log(module, level, message):
    appDir = os.path.dirname(os.path.realpath(__file__))
    appDir += "/Logs/"
    if os.path.exists(appDir) == False:
       os.mkdir(appDir)
    t = datetime.datetime.now()
    logName = appDir + t.strftime("Log_" + "%d_%m_%y_.csv")
    dateString = t.strftime("%d/%m/%y")
    timeString = t.strftime("%H:%M:%S")
    csvString = dateString + "," + timeString + "," + module + "," + level + "," + message + "\n"
    if os.path.exists(imageFile):
        file = open(logName, "a")
    else:
        file = open(logName, "w")
        file.write("Date,Time,Module,Level,Message\n")
    file.write(csvString)
    file.close()
    print("[" + module + "] " + level + ": " + message)
    
	

# Sends an email with a list of attachments through an SMTP server
def send_email(smtp_address, smtp_password, toaddr, fromaddr, subject, body, attachments):
   msg = MIMEMultipart()
   msg['From'] = fromaddr
   msg['To'] = toaddr
   msg['Subject'] = subject
   msg.attach(MIMEText(body, 'plain'))
   
   for attachment in attachments:
       filename = os.path.basename(attachment)
       attachment = open(attachment, "rb")
       part = MIMEBase('application', 'octet-stream')
       part.set_payload((attachment).read())
       encoders.encode_base64(part)
       part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
       msg.attach(part)

   try:
      server = smtplib.SMTP('smtp.gmail.com', 587)
      server.starttls()
      server.login(smtp_address, smtp_password)
      text = msg.as_string()
      server.sendmail(fromaddr, toaddr, text)
      server.quit()
   except:
      write_log("EMAIL", "ERROR", "Unable to send email.")

if __name__ == "__main__":
    #Configure the script here
    from_addr = "jonathan84clark@gmail.com"
    to_addr = "jonathan84clark@gmail.com"
    body = "Please unsubscribe me"
    subject = "Please unsubscribe me"
    rate = 5 # Currently set to run every minute
    emailsToSend = 10
    for i in range(0, emailsToSend):
        attachments = [] # For now we will have no attachments this may change later
        send_email(from_addr, "NICE TRY", to_addr, from_addr, subject, body, attachments)
        time.sleep(rate) # Capture a picture every ten minutes then email it to the security address
		    
	    
	
    