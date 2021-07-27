import pyb, machine, micropython
micropython.alloc_emergency_exception_buf(100)
from pyb import I2C

class I2C_Report: 
    
    def int_cb(line):
        global read_flag
        read_flag=1
        
    COMMs_PR=pyb.Pin('X19', pyb.Pin.OUT_PP)
    try:    
        COMMs_RP=pyb.ExtInt(pyb.Pin('X5'), pyb.ExtInt.IRQ_FALLING, pyb.Pin.PULL_UP, int_cb)
        COMMs_RP.disable()
        print('Configured COMMs_RP interrupt (line 4) on X5')
    except:
        try:
            print('Attempting to enable COMMs_RP.')
            COMMs_RP.enable()
        except:
            print('Error in COMMs_IN initialization.')
    
    SLAVE_ADDRESS = 0x42
    BAUDRATE = 100000
    try:
        i2c_slave = I2C(2, I2C.SLAVE, addr=SLAVE_ADDRESS, baudrate=BAUDRATE)
        print('I2C line set up.')
    except:
        print('Error initializing I2C.')
      
    def __init__(self):
        I2C_Report.COMMs_PR.low()
        print('COMMs_OUT bit set low.')
        I2C_Report.COMMs_RP.enable()
        print('COMMs_IN trigger listening.')
        
    def write(self,message):    
        
        WRITE_ATTEMPTS=3
        
        global read_flag
        read_flag=0
        
        message=message+'::' # :: are used as message termination code
        message_out='Sending ' + message + ' to Raspberry pi.'
        print(message_out)
        
        msg=bytes(message, 'utf-8')
        
        for j in msg:
            
            I2C_Report.COMMs_PR.high()
            pyb.delay(50)
            I2C_Report.COMMs_PR.low()
            #pyb.delay(50)
            sent=0
            
            #for i in range(WRITE_ATTEMPTS):
            count=0   
            
            try:
                I2C_Report.i2c_slave.send(j)
                sent=1
            except:
                return('Error writing byte.')
                    
            while sent:
                if read_flag==1:
                    read_flag=0
                    break
                    
                count=count+1
                if count>50000:
                    return('Byte sent; no ACK received.')
    
            if sent==0:
                return('Timed out writing bytes.')
                
        return('Transmission successful!')
          
    
    def read(self):   
        
        READING=1
        READ_ATTEMPTS=3
        TIMEOUT=500000
        
        global read_flag
        read_flag=0
        
        msg_returned=str()
        count=0
        
        while READING:
            
            if read_flag==1:
                read_flag=0
                got_it=0
                
                for i in range(READ_ATTEMPTS):
                    try:
                        return_byte= I2C_Report.i2c_slave.recv(1)
                        got_it=1
                        msg_returned= msg_returned + return_byte.decode("utf-8") 
                        #print(msg_returned)
                    except:
                        print('Error reading byte.')
                        
                    if got_it:
                        #Send ACKNOWLEDGE to Raspberry pi; READY for NEXT transmission
                        I2C_Report.COMMs_PR.high()
                        pyb.delay(50)
                        I2C_Report.COMMs_PR.low()
                        if len(msg_returned)>2 and msg_returned[-2:]=='::':
                            return(msg_returned)
                        break
                if got_it==0:
                    return('Failed to read byte.')   
            else:
                count=count+1
                if count>TIMEOUT:
                    return('Timeout reading I2C.')
                        






