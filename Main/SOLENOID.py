# This contains a list of functions developed for Meldrum's NSF-OTIC project
import pyb, machine
import  math, sys
import micropython
micropython.alloc_emergency_exception_buf(100)

class Push_Valve:
    """
    Lee class creates an interface to Lee LHLA2431411H 3-way valves
    Supported methods:
      reset()
      set()
    """
        
    def get_valve_configs (valve_number):
        Data=list()
        with open('config_valves.csv','r') as file:
            for line in file:
                line=line.rstrip('\r')
                line=line.rstrip('\n')
                Data.append(line.split(','))
        return Data[valve_number][:]
    
    def __init__(self, valve_number):
        
        # Get pin assignments from config_valves.csv on Pyboard
        config_list=Push_Valve.get_valve_configs(valve_number+1)   
        self.name=str(config_list[1])
        init_string="Configuring " + self.name
        print(init_string)
        pyb.delay(250)
        
        if valve_number==1:
          self.enable=pyb.Pin(pyb.Pin.cpu.B4, pyb.Pin.OUT_PP)
        elif valve_number==2:
          self.enable=pyb.Pin(pyb.Pin.cpu.A15, pyb.Pin.OUT_PP)
        else:
          print('Invalid valve number.')
            
        self.ctrl1=pyb.Pin(str(config_list[3]), pyb.Pin.OUT_PP)
        self.ctrl2=pyb.Pin(str(config_list[4]), pyb.Pin.OUT_PP)
        
        init_string="Control-1 pin:" + config_list[3]
        print(init_string)
        pyb.delay(250)
        
        init_string="Control-2 pin:" + config_list[4]
        print(init_string)
        pyb.delay(250)
        
        init_string="Enable pin:" + str(self.enable)
        print(init_string)
        pyb.delay(250)
        
        self.enable.high()
        self.ctrl1.low()
        self.ctrl2.low()
        
    def set(self, position):
        if position=='Open':
          out_string=self.name + " set in open position."
          print(out_string)
          self.enable.low()
          pyb.delay(50)
          self.ctrl1.low()
          self.ctrl2.high()
          pyb.delay(50)
          self.ctrl1.low()
          self.ctrl2.low()
          pyb.delay(50)
          self.enable.high()
          
        elif position=='Closed':
          out_string=self.name + " set in closed position."
          print(out_string)
          self.enable.low()
          pyb.delay(50)
          self.ctrl1.high()
          self.ctrl2.low()
          pyb.delay(50)
          self.ctrl1.low()
          self.ctrl2.low()
          pyb.delay(50)
          self.enable.high()
          
        else:
          print("Push valve command not recognized; Use Open or Closed")
        


