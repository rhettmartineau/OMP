# boot.py -- run on boot-up
# can run arbitrary Python, but best to keep it minimal

#import machine
#import micropython
#micropython.alloc_emergency_exception_buf(100)

#pyb.main('main.py') # main script to run after this one
#pyb.usb_mode('VCP+MSC') # act as a serial and a storage device
#pyb.usb_mode('VCP+HID') # act as a serial device and a mouse

import pyb, os
from pyb import LED, ADC
from lcd_api import LcdApi
from pyb import I2C, delay, millis
from pyb_i2c_lcd import I2cLcd
#from pyb import UART
from pyb import Pin
#import MCP9808
from OTIC import buildLogFilename as blf

#Temperature probe calibration terms
SLOPE=224.09 #These are used to convert raw voltage into temperature readings
INTERCEPT=-332.9

# PID control parameters
T=1 #This is the sample period in sec
Kp=2.75 #This is the basic proportional gain
Ti=750 #This is the integral constant
Td=0 #This is the derivative constant

# Per Zeigler-Nichols
# Kp=0.65*Kc (Proportional value at oscillation; Kc is critical gain producing oscillation)
# Ti= 0.5*Pc (The period of the oscillation, when run as P controller with value Kc
# Td= 0.12*Pc

Ki=Kp/Ti*T  #Integral constant in standard form
Kd=Kp*Td/T  #Derivative constant in standard form

#Ki=0  #Set to 0 for initial tuning
#Kd=0  #Set to 0 for initial tuning

DC_max=85  #Max ON time to protect heater; DC heating can damage element if voltages aren't matched

# Controller setpoint, in degrees C
displayVar=65
verString="v9-Sep-20"

def heater_cb(t):
    global heater_toggle
    global heaterEdge
    heaterEdge=1
    if heater_toggle==0:
        heater_toggle=1
    else:
        heater_toggle=0
        
def comms_cb(t):
    global comms_toggle
    global commsEdge
    commsEdge=1
    if comms_toggle==0:
        comms_toggle=1
    else:
        comms_toggle=0

CLOCK=168000000           #Base board clock frequency (Hz)
PRESCALER=168
#TIMER_FREQ=CLOCK/PRESCALER        #Use prescaler=168 for a 1 MHz timer

heater_pulse=Pin('Y3', Pin.OUT_PP)
heater_ready=Pin('X5', Pin.OUT_PP)
temperature_monitor=pyb.ADC(Pin('X12'))

redLED=1
writeLED=LED(redLED)
writeLED.off()

RESOLUTION=4096
ANALOG_IN_VOLTAGE=3.3

heater_ready.low()

heater_toggle=0
heaterEdge=0
comms_toggle=0
commsEdge=0
LOGGING=1

# The PCF8574 has a jumper selectable address: 0x20 - 0x27
DEFAULT_I2C_ADDR = 0x27
i2c = I2C(1, I2C.MASTER)
lcd = I2cLcd(i2c, DEFAULT_I2C_ADDR, 4, 20)
lcd.putstr("LCD active.\n")
delay(500)
lcd.clear()

rtc=pyb.RTC() #This heater board seems to have issue with RTC battery; no date can be saved for logger
filename, timeZero, timeTuple =blf(rtc,'temp')
delay(500)
filename='log/'+filename
lcd.putstr(filename)

heater_timer=pyb.Timer(2)      # Use heater_timer to trigger PID control iterations
comms_timer=pyb.Timer(4)       # Use comms_timer to trigger logging to SD card
heater_timer.init(freq=1)      # Use a 1-sec interval; duty cycle will be adjusted in terms of % of 1 sec to be ON
pyb.delay(500)
comms_timer.init(freq=1)       # Update LCD, SD every 1 sec
heater_timer.callback(heater_cb)
comms_timer.callback(comms_cb)

e_integral=0 #These are used to initiate error terms in loop below
e=0
temperature=25
tempStr='25\n'
DC=0
count=0
fault=0
FAULT=0

while True:
    
    if commsEdge:
        commsEdge=0

        if comms_toggle:
            
            if LOGGING:
                writeLED.on()
                f=open(filename, 'a')
                f.write(fileWriteString)
                f.close()
                writeLED.off()
            
            lcd.clear()
            lcd.putstr("Actual: %s" % tempStr )
            lcd.putstr("Setpoint: %s \n" % displayVar )
            lcd.putstr("DC: %f \n" % DC)
            lcd.putstr(verString) #Display software version to LCD
            
    if heaterEdge:
        heaterEdge=0      
             
        if heater_toggle:
            
            if DC>DC_max:
              DC=DC_max
            
            if DC==DC_max:
                fault=fault+1
                
            if fault>60:
                FAULT=1
                DC=1
                heater_pulse.low()
                verString="v9-Sep-20" + "      FAULT"
                LOGGING=0
                  
            if DC<1:
              DC=1
            
            if FAULT==0:
                frequency=(DC/100*T)**-1
                heater_pulse.low()
            
            x=range(3)
            temperature=0
            for i in x:
                temperature_raw=temperature_monitor.read()/RESOLUTION*ANALOG_IN_VOLTAGE
                temperature=temperature+temperature_raw*SLOPE+INTERCEPT
            temperature=temperature/len(x)
            tempStr=str(temperature)+'\n'
            
            e_deriv=e #This is the last cycle's error term
            e=float(displayVar)-temperature #This is the new error term
            e_deriv=(e-e_deriv) #This is the change in e over last cycle
            e_integral=e_integral+e #This is the integrated error
            
            if abs(e)<1.5:
                count=count+1
            if abs(e)>2:
                count=0
            if count>30:
                LOGGING=0
                heater_ready.high()
                verString="v9-Sep-20" + "         OK"
            
            if FAULT==0:
                DC=Kp*e + Ki*e_integral + Kd*e_deriv
            else:
                DC=1
                
            if DC>DC_max:
              DC=DC_max
            if DC<1:
              DC=1
          
            ignore1, currentTime, ignore2 =blf(rtc,'temp')
            time_in_secs=str(currentTime-timeZero)
            fileWriteString=time_in_secs+','+tempStr
            heater_timer.freq(frequency)
        else:
            if FAULT==0:
                heater_pulse.high()
                frequency=( (100-DC)/100*T )**-1
                heater_timer.freq(frequency)  

# 