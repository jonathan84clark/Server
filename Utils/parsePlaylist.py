import csv 
import requests 
import xml.etree.ElementTree as ET 
import os

  
def parseXML(xmlfile): 
  
    # create element tree object 
    tree = ET.parse(xmlfile) 
  
    # get root element 
    root = tree.getroot() 
  
    # create empty list for news items 
    newsitems = [] 
    
  
    # iterate news items 
    for item in root[1][0]: 
        print(item.attrib["src"])
        os.system("cp " + str(item.attrib["src"]) + " C:\\Users\\jonat\\Desktop\\MusicBosie")
        
      
    # return news items list 
    return newsitems 
  
  

def main(): 
    # load rss from web to update existing xml file 
    loadRSS() 
  
    # parse xml file 
    newsitems = parseXML('topnewsfeed.xml') 
  
    # store news items in a csv file 
    savetoCSV(newsitems, 'topnews.csv') 
      
      
if __name__ == "__main__": 
  
    # calling main function 
    parseXML("C:\\Users\\jonat\\Music\\Playlists\\boise.wpl") 