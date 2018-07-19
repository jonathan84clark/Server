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

# Captures an image from the onboard webcamera
def capture_picture(imagePath):
   try:
       os.system('./image.sh')
       #cap = cv2.VideoCapture(0)
       #ret, frame = cap.read()
       #rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
       #out = cv2.imwrite(imagePath, frame)
       #cap.release()
   except:
       write_log("CAMERA", "ERROR", "Unable to capture picture.")

if __name__ == "__main__":
    from_addr = "jonathan84clark@gmail.com" #sys.argv[1]
    #email_password = str(sys.argv[1]).strip()
    #email_password = email_password.replace("\n\r", "")
    #print(email_password)
    to_addr = "jonathan84clark@gmail.com" #sys.argv[3]
    appDir = os.path.dirname(os.path.realpath(__file__))
    #appDir += "/Pictures/"
    while (True):
        t = datetime.datetime.now()
        dateTimeStr = t.strftime("%d_%m_%y_%H_%M_%S")
        imageFile = appDir + "/image.jpeg"
        print(imageFile)
        if os.path.exists(appDir) == False:
           os.mkdir(appDir)
        capture_picture(imageFile)
        time.sleep(15)
        if os.path.exists(imageFile):
           write_log("MAIN", "INFO", "Sending email to: " + to_addr)
           attachments = []
           attachments.append(imageFile)
           subject = "Security image: " + dateTimeStr
           body = "Security image: " + dateTimeStr
           send_email(from_addr, "YOUR PASSWORD", to_addr, from_addr, subject, body, attachments)
        time.sleep(600) # Capture a picture every ten minutes then email it to the security address
		    
	    
	
    