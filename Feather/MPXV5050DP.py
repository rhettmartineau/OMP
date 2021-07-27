import pyb, machine
import micropython
micropython.alloc_emergency_exception_buf(100)

class MPXV5050DP:
  """
  MPXV5050DP Class creates an interface to the differential pressure sensor
  Supported methods:
    read() Gets current pressure; sets DIO line HIGH if over threshold
    set_threshold(value) Set threshold in units of psi
    reset() Sets interrupt output pin low
  """
  
  RESISTOR_1=47000     #These are the resistors for voltage divider
  RESISTOR_2=100000
  DIVIDER_SCALAR=RESISTOR_1/(RESISTOR_1+RESISTOR_2)
  ADCresolution=4096
  
  def set_threshold(self, threshold):
    self.threshold=threshold
    print('Threshold set at %s.' %threshold)
    
  def get_threshold(self):
    return self.threshold
    
  def read(self):
    accum=0
    for i in range(0,10):
      voltage_in=self.voltage_pin.read()/MPXV5050DP.ADCresolution
      v0=voltage_in/self.scalar
      pressure_Kpa=(v0/5-0.04)/0.018
      pressure_psi=pressure_Kpa*0.14504
      accum=accum+pressure_psi
    pressure_psi=accum/10
    
    if pressure_psi>self.threshold:
      self.interrupt_pin.high()
    return pressure_psi
    
  def reset(self):
    self.interrupt_pin.low()

  def __init__(self):
    self.scalar=MPXV5050DP.DIVIDER_SCALAR
    self.interrupt_pin=pyb.Pin('A1', pyb.Pin.OUT_PP)
    self.voltage_pin=pyb.ADC('A2')
    self.interrupt_pin.low()
    #self.threshold=0.1
    
    
    Data=list()
    with open('config/threshold.csv','r') as file:
        for line in file:
            Data=line.split(',')
            self.threshold=float(Data[1])
            
       
