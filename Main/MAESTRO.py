# This contains a list of functions developed for Meldrum's NSF-OTIC project
import pyb, machine
from pyb import Switch, LED
import  math, sys
import micropython
micropython.alloc_emergency_exception_buf(100)

class Pump:
    """
    Pump class creates an interface to BioChem Maestro Piston Pumps
    Supported methods:
      home()
      reset()
      dispense(volume, rate)
    """
    # TIMER CONSTANTS
    CLOCK=168000000           #Base board clock frequency (Hz)
    PRESCALER=84
    TIMER_FREQ=CLOCK/PRESCALER        #Use prescaler=168 for a 1 MHz timer
    ALPHA=0.0314159265358979  #Motor step angle (radians)

    # EXIT CODES
    RUNNING=-1                #Indicates running state after pulse cycles initiated
    SUCCESS=0                 #Indicates successful start/stop of a pulse train
    USER_INTERRUPT=3          #Indicates user button pressed during start/stop cycle
    BUTTON=2
    START=4
    PLATEAU=5
    DECELERATE=6
    HOME=9
    LIMIT=8
    FINISH=7
    
    global errorCode
    errorCode=9
    
    def get_pump_configs (pump_number):
        Data=list()
        with open('config_pumps.csv','r') as file:
            for line in file:
                line=line.rstrip('\r')
                line=line.rstrip('\n')
                Data.append(line.split(','))
        return Data[pump_number][:]
    
    def userButton_cb():
        global errorCode
        errorCode=Pump.USER_INTERRUPT              #Toggle the LED between on and off.
        #errorCode=Pump.BUTTON
  
    def limit_cb(_):
        global errorCode
        #if Pump.direction==1:     #This was direction==1:
        errorCode=Pump.LIMIT
  
    def drive_cb(t):
        global stepper_flag
        global toggle
        toggle=1
      
        if stepper_flag==0:
            stepper_flag=1
        else:
            stepper_flag=0    
        
    def __init__(self, pump_number):
        self.pump_number=pump_number
        
        # Get pin assignments from configs_pump.csv on Pyboard
        config_list=Pump.get_pump_configs(pump_number)
        # Setup LED indicators
        redLED=1
        greenLED=2
        yellowLED=3
        blueLED=4
        
        self.RUNled=LED(blueLED)
        self.ERRORled=LED(redLED)
        self.userButton=Switch()
        self.userButton.callback(Pump.userButton_cb)
        
        self.name=str(config_list[1])
        init_string="Configuring " + self.name + " pump."
        print(init_string)
        pyb.delay(1000)
        
        self.interrupt_pinStr=config_list[3]
        self.interrupt_pin = pyb.ExtInt(pyb.Pin(self.interrupt_pinStr), pyb.ExtInt.IRQ_FALLING, pyb.Pin.PULL_UP, Pump.limit_cb)
        self.limit_monitor= pyb.Pin(pyb.Pin(self.interrupt_pinStr), pyb.Pin.IN)
        
        pyb.delay(500)
        self.interrupt_pin.disable()
        interrupt_string="Interrupt set on pin " + self.interrupt_pinStr
        print(interrupt_string)

        if self.name=='Seawater':
            print('Setting up pressure interrupt.')
            self.pressure_interrupt_pin = pyb.ExtInt(pyb.Pin('X10'), pyb.ExtInt.IRQ_RISING, pyb.Pin.PULL_UP, Pump.limit_cb)
            pyb.delay(500)
            self.pressure_interrupt_pin.disable()
            interrupt_string="Pressure interrupt set on pin X10."
            print(interrupt_string)

        pyb.delay(500)
        line=self.interrupt_pin.line()
        print(line)
        self.max_volume=config_list[2]
        self.reset_pin=pyb.Pin(config_list[4], pyb.Pin.OUT_PP)
        self.enable_pin=pyb.Pin(config_list[5], pyb.Pin.OUT_PP)
        self.dir_pin=pyb.Pin(config_list[6], pyb.Pin.OUT_PP)
        self.step_pin=pyb.Pin(config_list[7], pyb.Pin.OUT_PP)
        
        self.reset_pin.low()
        pyb.delay(30)
        self.reset_pin.high()
        self.enable_pin.high()
          
    def report(self):
        max_volume_string="Stroke volume: " + self.max_volume
        return max_volume_string
    
    def dispense(self, plateau_steps, dispensings, speed):   
        direction=1  #This was in the dispense function, below
        print("Dispensing...")
        if self.name=='Seawater':
            self.pressure_interrupt_pin.enable()
        self.interrupt_pin.enable()
        print("Interrupt enabled.")
        pyb.delay(300)
        
        global errorCode
        global stepper_flag
        global toggle

        #OMEGA_PRIME=300             #Acceleration, radians per second squared
        #C_MIN=451 #39 
        m_plateau=plateau_steps     #15000 is 80% aspirate/dispense steps for 1/8 microstepping
        cycles=0
        cycles_STOP=2*dispensings
        
        errorCode=Pump.START
        print("Starting pump...")

        self.RUNled.on()
        self.ERRORled.off()
        self.enable_pin.low()
        
        while (errorCode!=Pump.SUCCESS):
          while (errorCode==Pump.START):
            
            if direction==-1:
              self.dir_pin.high()  #high is aspirate
              C_MIN=(speed-102.3)/-0.0051 #from 100% of 491, 0% of 20000 C_n
            else:
              C_MIN=491
              OMEGA_PRIME=300
              self.dir_pin.low()
            
            C_0=int(0.676*Pump.CLOCK/Pump.PRESCALER*math.sqrt(2*Pump.ALPHA/OMEGA_PRIME))
            C_n=C_0
            toggle=0                  #Set to 1 in callback; set to 0 after processing; implements edge detection
            i=1
            stepper_flag=0            #toggled in the stepper callback to generate 50% DC HI pulse
            vol=0

            Stepper=pyb.Timer(8,freq=0.1)      #Specify the timer ID
    
            Stepper.callback(Pump.drive_cb)
            Stepper.init(prescaler=Pump.PRESCALER, period=C_0)       
            errorCode=Pump.BUTTON
            
          while (errorCode==Pump.BUTTON):
            if toggle:
              toggle=0
              if stepper_flag:
                self.step_pin.high()
              else:
                self.step_pin.low()
                C_n=int(C_n-2*C_n/(4*i+1))
                i=i+1
                Stepper.period(C_n)
        
                if C_n<C_MIN: 
                  errorCode=Pump.PLATEAU
                  m=0
                  i_ramp=i
                  i=-i
                  m_steps=m_plateau-2*i_ramp
        
            else:
              pass
      
          while (errorCode==Pump.PLATEAU):
            if toggle:
              toggle=0
              if stepper_flag:
                #self.enable_pin.low()
                self.step_pin.high()
              else:
                self.RUNled.off()
                self.step_pin.low()
                #C_n=int(C_n-2*C_n/(4*i+1)) #This changed 9/6
                m=m+1
                Stepper.period(C_n)
                
                if m>m_steps:
                  errorCode=Pump.DECELERATE
                  n=0
        
            else:
              pass
      
          while (errorCode==Pump.DECELERATE):
            if toggle:
              toggle=0
              if stepper_flag:
                self.step_pin.high()
              else:
                if i<0:
                  self.step_pin.low()
                  C_n=int(C_n-2*C_n/(4*i+1))
                  #print("Iterates: %i" %i)
                  #vol=vol+2.5
                  Stepper.period(C_n)
                  i=i+1
                  n=n+1
                else:
                  errorCode=Pump.SUCCESS
                  Stepper.deinit()
            else:
              pass
            
          if (errorCode==Pump.USER_INTERRUPT):
            print("Interrupt detected (USER_INTERRUPT). Pumping stopped")
            Stepper.deinit()
            self.enable_pin.high()
            self.RUNled.off()
            self.ERRORled.on()
            pyb.delay(1000)
            self.ERRORled.off()
            #self.interrupt_pin = pyb.ExtInt(pyb.Pin(self.interrupt_pinStr), pyb.ExtInt.IRQ_FALLING, pyb.Pin.PULL_UP, None)
            self.interrupt_pin.disable()
            print("Successful shut-down.")
            sys.exit()
            
          if (errorCode==Pump.SUCCESS):
            print("Pump cycle successfully completed.")
            i_total=i_ramp+n+m
            vol=2.5*i_total
            print("Volume: %f" %vol)
            print("Steps in plateau phase: %i" %m)
            print("Iterates: %i" %i_total)
            print("C_MIN: %i" %C_MIN)
            print("Final C_n: %i" %C_n)
            print("Final iterates: %i" %n)
            #stop_micros = micros.counter()
            #total_time=(stop_micros-start_micros)/1e6
            #print("Final time: %f" %total_time)
                        
            cycles=cycles+1
            direction=direction*-1
    
            if cycles!=cycles_STOP:
              errorCode=Pump.START
              pyb.delay(100)
              print("Reversing...")
              self.enable_pin.low()
              pyb.delay(50)
            else:
              errorCode=Pump.FINISH
      
          if (errorCode==Pump.FINISH):
            cycles=0
            print("Cycles completed!")
            self.RUNled.off()
            self.ERRORled.on()
            self.enable_pin.high()
            pyb.delay(1000)
            self.ERRORled.off()
            errorCode=Pump.SUCCESS
            Stepper.deinit()
            #self.interrupt_pin = pyb.ExtInt(pyb.Pin(self.interrupt_pinStr), pyb.ExtInt.IRQ_FALLING, pyb.Pin.PULL_UP, None)
            self.interrupt_pin.disable()
            #sys.exit()
    
          if (errorCode==Pump.LIMIT):
            self.enable_pin.high()
            Stepper.deinit()
            #self.interrupt_pin = pyb.ExtInt(pyb.Pin(self.interrupt_pinStr), pyb.ExtInt.IRQ_FALLING, pyb.Pin.PULL_UP, None)
            self.interrupt_pin.disable()
            print("Interrupt detected (LIMIT). Pumping stopped")
            self.RUNled.off()
            self.ERRORled.on()
            pyb.delay(1000)
            self.ERRORled.off()
            print("Successful shut-down.")
            errorCode=Pump.SUCCESS
            #sys.exit()
    
    def home(self):   
        direction=-1  #This was in the dispense function, below
        print("Homing...")
        if self.name=='Seawater':
            self.pressure_interrupt_pin.enable()
        self.interrupt_pin.enable()
        print("Interrupt enabled.")
        pyb.delay(300)
        
        global errorCode
        global stepper_flag
        global toggle

        OMEGA_PRIME=300             #Acceleration, radians per second squared
        C_MIN=600 #39
        m_plateau=18000            #full aspirate/dispense steps for 1/8 microstepping
        cycles=0
        cycles_STOP=2
        
        errorCode=Pump.START
        print("Starting pump...")
        
        if self.limit_monitor.value()==0:
            print('Pump already in home position.')
            errorCode=Pump.HOME
            
        self.RUNled.on()
        self.ERRORled.off()
        self.enable_pin.low()
        
        while (errorCode!=Pump.SUCCESS):
          while (errorCode==Pump.START):
            C_0=int(0.676*Pump.CLOCK/Pump.PRESCALER*math.sqrt(2*Pump.ALPHA/OMEGA_PRIME))
            C_n=C_0
            toggle=0                  #Set to 1 in callback; set to 0 after processing; implements edge detection
            i=1
            stepper_flag=0            #toggled in the stepper callback to generate 50% DC HI pulse
            vol=0

            Stepper=pyb.Timer(8,freq=0.1)      #Specify the timer ID
    
            if direction==-1:
              self.dir_pin.high()  #high is aspirate
            else:
              self.dir_pin.low()
    
            Stepper.callback(Pump.drive_cb)
            Stepper.init(prescaler=Pump.PRESCALER, period=C_0)       
            errorCode=Pump.BUTTON

          while (errorCode==Pump.BUTTON):
            if toggle:
              toggle=0
              if stepper_flag:
                self.step_pin.high()
              else:
                self.step_pin.low()
                C_n=int(C_n-2*C_n/(4*i+1))
                i=i+1
                Stepper.period(C_n)
        
                if C_n<C_MIN:
                  errorCode=Pump.PLATEAU
                  m=0
                  i_ramp=i
                  i=-i
                  m_steps=m_plateau-2*i_ramp
        
            else:
              pass
      
          while (errorCode==Pump.PLATEAU):
            if toggle:
              toggle=0
              if stepper_flag:
                #self.enable_pin.low()
                self.step_pin.high()
              else:
                self.RUNled.off()
                self.step_pin.low()
                C_n=int(C_n-2*C_n/(4*i+1))
                m=m+1
                Stepper.period(C_n)
                
                if m>m_steps:
                  errorCode=Pump.DECELERATE
                  n=0
        
            else:
              pass
      
          while (errorCode==Pump.DECELERATE):
            if toggle:
              toggle=0
              if stepper_flag:
                self.step_pin.high()
              else:
                if i<0:
                  self.step_pin.low()
                  C_n=int(C_n-2*C_n/(4*i+1))
                  #print("Iterates: %i" %i)
                  #vol=vol+2.5
                  Stepper.period(C_n)
                  i=i+1
                  n=n+1
                else:
                  errorCode=Pump.SUCCESS
                  Stepper.deinit()
            else:
              pass
            
          if (errorCode==Pump.USER_INTERRUPT):
            print("Interrupt detected (USER_INTERRUPT). Pumping stopped")
            Stepper.deinit()
            self.enable_pin.high()
            self.RUNled.off()
            self.ERRORled.on()
            pyb.delay(1000)
            self.ERRORled.off()
            #self.interrupt_pin = pyb.ExtInt(pyb.Pin(self.interrupt_pinStr), pyb.ExtInt.IRQ_FALLING, pyb.Pin.PULL_UP, None)
            try:
                self.interrupt_pin.disable()
            except:
                print('Interrupt pin didnt need to be disabled.')
                
            print("Successful shut-down.")
            sys.exit()
            
          if (errorCode==Pump.SUCCESS):
            print("Pump cycle successfully completed.")
            i_total=i_ramp+n+m
            vol=2.5*i_total
            print("Volume: %f" %vol)
            print("Steps in plateau phase: %i" %m)
            print("Iterates: %i" %i_total)
            print("C_MIN: %i" %C_MIN)
            print("Final C_n: %i" %C_n)
            print("Final iterates: %i" %n)
            #stop_micros = micros.counter()
            #total_time=(stop_micros-start_micros)/1e6
            #print("Final time: %f" %total_time)
                        
            cycles=cycles+1
            direction=direction*-1
    
            if cycles!=cycles_STOP:
              errorCode=Pump.START
              pyb.delay(100)
              print("Reversing...")
              self.enable_pin.low()
              pyb.delay(50)
            else:
              errorCode=Pump.FINISH
      
          if (errorCode==Pump.FINISH):
            cycles=0
            print("Cycles completed!")
            self.RUNled.off()
            self.ERRORled.on()
            self.enable_pin.high()
            pyb.delay(1000)
            self.ERRORled.off()
            errorCode=Pump.SUCCESS
            Stepper.deinit()
            #self.interrupt_pin = pyb.ExtInt(pyb.Pin(self.interrupt_pinStr), pyb.ExtInt.IRQ_FALLING, pyb.Pin.PULL_UP, None)
            self.interrupt_pin.disable()
            #sys.exit()
    
          if (errorCode==Pump.LIMIT):
            self.enable_pin.high()
            Stepper.deinit()
            #self.interrupt_pin = pyb.ExtInt(pyb.Pin(self.interrupt_pinStr), pyb.ExtInt.IRQ_FALLING, pyb.Pin.PULL_UP, None)
            self.interrupt_pin.disable()
            print("Interrupt detected (LIMIT). Pumping stopped")
            self.RUNled.off()
            self.ERRORled.on()
            pyb.delay(1000)
            self.ERRORled.off()
            print("Successful shut-down.")
            errorCode=Pump.SUCCESS
            #sys.exit()

          if (errorCode==Pump.HOME):
            self.enable_pin.high()
            #Stepper.deinit()
            #self.interrupt_pin = pyb.ExtInt(pyb.Pin(self.interrupt_pinStr), pyb.ExtInt.IRQ_FALLING, pyb.Pin.PULL_UP, None)
            self.interrupt_pin.disable()
            print("Home detected. Pumping stopped")
            self.RUNled.off()
            self.ERRORled.on()
            pyb.delay(1000)
            self.ERRORled.off()
            print("Successful shut-down.")
            errorCode=Pump.SUCCESS
            #sys.exit()
            
#pump_1=Pump(3)
#print(pump_1.interrupt_pin)
#pump_1_status=pump_1.report()
#print(pump_1_status)
#pump_1.dispense(500, 500)
#print(pump_1.LIMIT)

#pump_1.dispense(500,500)