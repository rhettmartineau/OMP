
# This contains a list of functions developed for Meldrum's NSF-OTIC project
import pyb, machine, micropython
micropython.alloc_emergency_exception_buf(100)
from pyb import I2C

print('Rev 7.')

COMMs_PR=pyb.Pin('X19', pyb.Pin.OUT_PP)
COMMs_PR.low()
print('Waiting for server to be ready.')

def int_cb(line):
  global read_flag
  read_flag=1
  
try:    
  COMMs_RP=pyb.ExtInt(pyb.Pin('X5'), pyb.ExtInt.IRQ_FALLING, pyb.Pin.PULL_UP, int_cb)
  print('Configured COMMs_RP interrupt (line 4) on X5')
except:
  try:
      print('Attempting to enable COMMs_RP.')
      COMMs_RP.enable()
  except:
      print('Error in COMMs_IN initialization.')
  
SLAVE_ADDRESS = 0x42
BAUDRATE = 100000
i2c_slave = I2C(2, I2C.SLAVE, addr=SLAVE_ADDRESS, baudrate=BAUDRATE)
print('I2C_2 initialized.\n')


pyb.delay(10000)

global read_flag
read_flag=0

COMMs_PR.high()
pyb.delay(50)
COMMs_PR.low()

iterates=0
counts=0
data_to_send=bytearray(1)

while True:
  iterates=iterates+1
  if read_flag==1:
      
      read_flag=0
      try:
        data = i2c_slave.recv(1)
      except OSError as exc:
        if exc.args[0] not in (5, 110):
          # 5 == EIO, occurs when master does a I2C bus scan
          # 110 == ETIMEDOUT
          print(exc)
      else:
        print("RECV: %r" % data)
        try:
          i2c_slave.send(data)
        except:
          print('Couldnt send bytes after read event.')
          
  if iterates>50000:      
    counts=counts+1
    msg='Waiting for comms from Raspi... '+str(counts)
    print(msg)
    iterates=0







