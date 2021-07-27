# This contains a list of functions developed for Meldrum's NSF-OTIC project
import pyb, machine, micropython
micropython.alloc_emergency_exception_buf(100)
from pyb import I2C
DELAY=250

SLAVE_ADDRESS = 0x42
BAUDRATE = 100000
i2c_slave = I2C(2, I2C.SLAVE, addr=SLAVE_ADDRESS, baudrate=BAUDRATE)
print('I2C_2 initialized.\n')

def int_cb(_):
  global interrupt_flag
  interrupt_flag=1
  
try:
  int_1=pyb.ExtInt(pyb.Pin('X5'), pyb.ExtInt.IRQ_FALLING, pyb.Pin.PULL_UP, int_cb)
except:
  pass

data=bytearray(3)
print(data)
while True:
  
  i2c_slave.send(data)
#except:
#  print('Failed to send...')
  

