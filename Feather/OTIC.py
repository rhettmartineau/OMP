import pyb
        
def buildLogFilename(rtc, logType):
  #'This function takes an rtc object and returns a filename'
    timeTuple=rtc.datetime()
    timeString='{0}-{1}-{2}-{3}-{4}-{5}_{6}Log.dat'.format(timeTuple[0], timeTuple[1], timeTuple[2], timeTuple[4], timeTuple[5], timeTuple[6], logType)
    timeStamp=timeTuple[3]*24*3600+timeTuple[4]*3600+timeTuple[5]*60+timeTuple[6]
    return timeString, timeStamp, timeTuple 
    










