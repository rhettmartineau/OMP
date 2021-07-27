#hardware platform: pyboard V1.1

import pyb, sys, math
from pyb import Switch, ExtInt
from pyb import Pin
from pyb import LED
import micropython
micropython.alloc_emergency_exception_buf(100)

# CONSTANT ASSIGNMENTS
redLED=1
greenLED=2
yellowLED=3
blueLED=4
RUNled=LED(blueLED)
ERRORled=LED(redLED)

p_out = Pin('Y4', Pin.OUT_PP)
dir_out= Pin('Y3', Pin.OUT_PP)
enable_out= Pin('X5', Pin.OUT_PP)
reset_out= Pin('X2', Pin.OUT_PP)
valve_out= Pin('Y5', Pin.OUT_PP)

valve_out.high()
pyb.delay(30)
valve_out.low()

reset_out.high()
enable_out.low()

CLOCK=168000000           #Base board clock frequency (Hz)
PRESCALER=83
TIMER_FREQ=CLOCK/PRESCALER        #Use prescaler=168 for a 1 MHz timer
ALPHA=0.0314159265358979  #Motor step angle (radians)

OMEGA_PRIME=300             #Acceleration, radians per second squared
C_MIN=451 #39
m_plateau=18000            #full aspirate/dispense steps for 1/8 microstepping

# EXIT CODES
RUNNING=-1                #Indicates running state after pulse cycles initiated
SUCCESS=0                 #Indicates successful start/stop of a pulse train
USER_INTERRUPT=3          #Indicates user button pressed during start/stop cycle
BUTTON=2
START=4
PLATEAU=5
DECELERATE=6
FINISH=7
LIMIT=8

cycles=0
cycles_STOP=2
direction=-1

errorCode=START

def limit_cb(_):
  global errorCode
  if direction==1:
    errorCode=LIMIT
  
def drive_cb(t):
      global stepper_flag
      global toggle
      toggle=1
      
      if stepper_flag==0:
        stepper_flag=1
      else:
        stepper_flag=0
    
def userButton_cb():
  global errorCode
  #errorCode=USER_INTERRUPT              #Toggle the LED between on and off.
  errorCode=BUTTON
  
ext = pyb.ExtInt(Pin('X20'), pyb.ExtInt.IRQ_FALLING, pyb.Pin.PULL_NONE, limit_cb)

print("Starting pump listener")

userButton=Switch() 
userButton.callback(userButton_cb)
RUNled.off()
ERRORled.off()
enable_out.high()


while (errorCode!=SUCCESS):
  
  while (errorCode==START):
    C_0=int(0.676*CLOCK/PRESCALER*math.sqrt(2*ALPHA/OMEGA_PRIME))
    print("C_0: %i" %C_0)
    
    C_n=C_0
    toggle=0                  #Set to 1 in callback; set to 0 after processing; implements edge detection
    i=1
    stepper_flag=0            #toggled in the stepper callback to generate 50% DC HI pulse
    vol=0
        
    micros = pyb.Timer(2, prescaler=83, period=0x3fffffff)
    micros.counter(0)
    start_micros = micros.counter()

    Stepper=pyb.Timer(1,freq=0.1)      #Specify the timer ID
    
    if direction==-1:
      dir_out.high()  #high is aspirate
    else:
      dir_out.low()
    
    Stepper.callback(drive_cb)
    Stepper.init(prescaler=PRESCALER, period=C_0)
    
    #if cycles>0:
    #  errorCode=BUTTON
    #else:
    #  errorCode=RUNNING
    errorCode=BUTTON
    
  while (errorCode==BUTTON):
    if toggle:
      toggle=0
      if stepper_flag:
        #RUNled.on()
        enable_out.low()
        p_out.high()
        
      else:
        #RUNled.off()
        p_out.low()
        C_n=int(C_n-2*C_n/(4*i+1))
        i=i+1
        #print("Iterates: %i" %i)
        Stepper.period(C_n)
        
        if C_n<C_MIN:
          #RUNled.off()
          errorCode=PLATEAU
          m=0
          i_ramp=i
          i=-i
          m_steps=m_plateau-2*i_ramp
        
    else:
      pass
      
  while (errorCode==PLATEAU):
    if toggle:
      toggle=0
      if stepper_flag:
        enable_out.low()
        p_out.high()
        
      else:
        #RUNled.off()
        p_out.low()
        #C_n=int(C_n-2*C_n/(4*i+1))
        m=m+1
        #print("Iterates: %i" %i)
        #Stepper.period(C_n)
        
        if m>m_steps:
          #RUNled.off()
          errorCode=DECELERATE
          n=0
        
    else:
      pass
      
      
  while (errorCode==DECELERATE):
    if toggle:
      toggle=0
      if stepper_flag:
        #RUNled.on()
        p_out.high()
        
      else:
        #RUNled.off()
        #p_out.low()
        if i<0:
          p_out.low()
          C_n=int(C_n-2*C_n/(4*i+1))
          #print("Iterates: %i" %i)
          #vol=vol+2.5
          Stepper.period(C_n)
          i=i+1
          n=n+1
        else:
          #RUNled.off()
          errorCode=SUCCESS
          Stepper.deinit()
          enable_out.high()

    else:
      pass
      
  if (errorCode==USER_INTERRUPT):
    print("Interrupt detected (USER_INTERRUPT). Pumping stopped")
    Stepper.deinit()
    RUNled.off()
    ERRORled.on()
    pyb.delay(1000)
    ERRORled.off()

  if (errorCode==SUCCESS):
    print("Pump cycle successfully completed.")
    i_total=i_ramp+n+m
    vol=2.5*i_total
    print("Volume: %f" %vol)
    print("Steps in plateau phase: %i" %m)
    print("Iterates: %i" %i_total)
    print("C_MIN: %i" %C_MIN)
    print("Final C_n: %i" %C_n)
    print("Final iterates: %i" %n)
    stop_micros = micros.counter()
    total_time=(stop_micros-start_micros)/1e6
    #print("Final time: %f" %total_time)
    #RUNled.off()
    cycles=cycles+1
    direction=direction*-1
    
    if cycles!=cycles_STOP:
      errorCode=START
      #pyb.delay(1000)
      pyb.delay(100)
      print("Restarting!")
      pyb.delay(50)
    else:
      errorCode=FINISH
      
  if (errorCode==FINISH):
    cycles=0
    print("Cycles completed!")
    RUNled.off()
    ERRORled.on()
    pyb.delay(1000)
    ERRORled.off()
    errorCode=SUCCESS
    enable_out.high()
    Stepper.deinit()
    ext = pyb.ExtInt(Pin('X20'), pyb.ExtInt.IRQ_FALLING, pyb.Pin.PULL_NONE, None)
    sys.exit
    
  if (errorCode==LIMIT):
    enable_out.high()
    Stepper.deinit()
   
    ext = pyb.ExtInt(Pin('X20'), pyb.ExtInt.IRQ_FALLING, pyb.Pin.PULL_NONE, None)

    print("Interrupt detected (LIMIT). Pumping stopped")
    
    RUNled.off()
    ERRORled.on()
    pyb.delay(1000)
    ERRORled.off()
    print("Successful shut-down.")
    errorCode=SUCCESS
    sys.exit































