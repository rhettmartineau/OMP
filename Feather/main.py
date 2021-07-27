# This contains a class definition for the Sensiron SLF3S-1300F Liquid Flow Sensor
import SENSIRION, MPXV5050DP, OTIC
import pyb

def start_stop_cb(_):
  global state_code
    
  if state_code=='waiting':
    state_code='starting'
  else:
    if state_code=='running':
      state_code='stopping'
      
def read_timer_cb(t):
  global read_flag
  read_flag=1

# Initialization block
global state_code
global read_flag

rtc=pyb.RTC()
returns=OTIC.buildLogFilename(rtc, 'flow')
fileString='log/' +returns[0]

state_code='waiting'
read_flag=0
#PRESSURE_THRESHOLD=1
MAX_VOL=500 #This is for scaling the analog out
            # 0-4095, with 4095 representing 500 ml
            
enable=pyb.Pin(pyb.Pin('D13'), pyb.Pin.OUT_PP)
pressure_sensor_power=pyb.Pin(pyb.Pin('D12'), pyb.Pin.OUT_PP)
pressure_sensor_power.high()
pressure_interrupt=pyb.Pin(pyb.Pin('A1'), pyb.Pin.OUT_PP)
pressure_interrupt.low()

flow_sensor=SENSIRION.SLF3S() #Instantiate flow sensor
pressure_sensor=MPXV5050DP.MPXV5050DP() #Instantiate pressure sensor
#pressure_sensor.set_threshold(PRESSURE_THRESHOLD)

pyb.delay(250)
start_stop_interrupt=pyb.ExtInt(pyb.Pin('A3'), pyb.ExtInt.IRQ_RISING, pyb.Pin.PULL_NONE, start_stop_cb)
print('Start/stop IRQ set up.')
pyb.delay(250)

read_timer=pyb.Timer(3,freq=0.1)      #Specify the timer ID
read_timer.callback(read_timer_cb)
total_flow=0
dac=pyb.DAC(1, bits=12)

while state_code!='closing':

  if state_code=='starting':
    print('Start signal received.')
    flow_sensor.start()
    start_stop_interrupt.disable()
    print('Interrupt disabled...')
    f=open(fileString, 'w')
    pyb.delay(250)
    start_stop_interrupt.enable()
    #start_stop_interrupt=pyb.ExtInt(pyb.Pin('A3'), pyb.ExtInt.IRQ_FALLING, pyb.Pin.PULL_NONE, start_stop_cb)
    read_timer.init(freq=5)   
    state_code='running'
  
  if state_code=='pressure limit':
    print('Pressure threshold exceeded. Stopping measurement. Pyboard interrupt thrown by MPXV5050DP.py.')
    state_code='stopping'
    pressure_interrupt.high()
  
  if state_code=='stopping':
    read_timer.deinit()
    flow_sensor.stop()
    f.close()
    pyb.delay(250)
    pressure_sensor_power.low()
    state_code='closing'

  if read_flag:
    read_flag=0
    pressure=pressure_sensor.read()
    
    #print('Pressure  :%s' %pressure)
    if pressure>pressure_sensor.get_threshold():
      state_code='pressure limit'
    data_in=flow_sensor.read()
    if data_in[3]==0:
      write_str=str(pressure) + '\t' + str(data_in[0])
      #print('Flowrate  :%s' %data_in[0])
    else:
      #print('Error reading SLF3S flow sensor.')
      write_str=str(pressure) + '\t' + str(-1)
    
    total_flow=total_flow+data_in[0]
    write_str=write_str+ '\t' + str(total_flow) + '\n'
    f.write(write_str)
    
    

print('Total flow: %s' %total_flow)
write_count=round(total_flow/MAX_VOL*4095)
if write_count>0 & write_count<4096:
  dac.write(write_count)
elif write_count<0:
  dac.write()
  print('Lower than 0 flow.')
else:
  dac.write(4095)
  print('Max flow exceeded.')

      















