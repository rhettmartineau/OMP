import pyb, machine, micropython
micropython.alloc_emergency_exception_buf(100)
from pyb import I2C

import I2C_PYBOARD_RASPI
port=I2C_PYBOARD_RASPI.I2C_Report()

while 1:
    msg=port.read()
    print(msg)
    
    if 'DATA' in msg:
        return_msg=port.write('ACK')
        print(return_msg)
        
        