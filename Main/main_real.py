# main.py -- put your code here!
import pyb
import MAESTRO, LEE, SOLENOID


try:
  seawater_pump=MAESTRO.Pump(1)
except:
  print('Seawater pump already configured.')

epv_1=SOLENOID.Push_Valve(1) #External push valve 1
threeway_valve=LEE.TWV()

epv_1.set('Closed')
threeway_valve.set('C')
  
pyb.delay(2000)

flowrate = pyb.ADC(pyb.Pin.board.Y12)
feather_power=pyb.Pin('Y1', pyb.Pin.OUT_PP)
start_stop=pyb.Pin('X9', pyb.Pin.OUT_PP)
start_stop.low()
feather_power.low()

pyb.delay(1000)
feather_power.high()
print('Waiting for Featherboard to boot up.')
pyb.delay(3000)
print('Sending start signal.')
start_stop.high()
print('Giving Featherboard moment to start flow sensor.')
pyb.delay(1000)
print('Pumping seawater.')
start_stop.low()

seawater_pump.dispense(500,500)
seawater_pump.dispense(500,500)

print('Finished pumping seawater.')
start_stop.high()
pyb.delay(250)
start_stop.low()

print('Giving Featherboard time to properly shut down.')
pyb.delay(3000)

measured_flowrate= flowrate.read()
display_str='ADC_flowrate: ' + str(measured_flowrate) + '\n'
print(display_str)
pyb.delay(3000)
print('Cutting power to the Featherboard.')
pyb.delay(1000)
feather_power.low()

threeway_valve.set('D')
epv_1.set('Open')
