import pyb, machine, micropython
micropython.alloc_emergency_exception_buf(100)
from pyb import I2C

import I2C_PYBOARD_RASPI
port=I2C_PYBOARD_RASPI.I2C_Report()
import SOLENOID
epv_1=SOLENOID.Push_Valve(1)
epv_2=SOLENOID.Push_Valve(2)
import LEE
threeway_valve=LEE.TWV()
import MAESTRO
Seawater_pump=MAESTRO.Pump(5)
Lysis_pump=MAESTRO.Pump(4)
Push_pump=MAESTRO.Pump(3)
Pull_pump=MAESTRO.Pump(1)
Dummy_pump=MAESTRO.Pump(2)

print('Configuring I/O for flow measurement')
flowrate = pyb.ADC(pyb.Pin.board.Y12)
feather_power=pyb.Pin('Y1', pyb.Pin.OUT_PP)
start_stop=pyb.Pin('X9', pyb.Pin.OUT_PP)
start_stop.low()
feather_power.low()
print('I/O for flow measurement configured.')

WRITE_ATTEMPTS=3
SENDING=1
RUNNING=1
MSG_GOOD=1
MSG_BAD=2
NO_MSG=3
status=NO_MSG

while RUNNING:
    
        status=NO_MSG
    
        msg=port.read()
                
        if '::' in msg:
            print('Received a transmission')
            msg=msg[:-2]
            
        else:
            if 'failed' in msg:
                print(msg)
                return_msg=msg
                continue
        
            if 'Time' in msg:
                print(msg)
                return_msg=msg
                continue
    
        if 'EPV' in msg:
            print('EPV in msg TRUE')
            if '1' in msg:
                if 'CLOSED' in msg:
                    epv_1.set('Closed')
                    return_msg='EPV 1 CLOSED.'
                    status=MSG_GOOD
                
                if 'OPEN' in msg:
                    epv_1.set('Open')
                    status=MSG_GOOD
                    return_msg='EPV 1 OPENED.'
            
            if '2' in msg:
                if 'CLOSED' in msg:
                    epv_2.set('Closed')
                    status=MSG_GOOD
                    return_msg='EPV 2 CLOSED.'
                
                if 'OPEN' in msg:
                    epv_2.set('Open')
                    status=MSG_GOOD
                    return_msg='EPV 2 OPENED.'
                             
            if not(status==MSG_GOOD):
                print('MSG is in fact BAD')
                return_msg='Error parsing EPV command; EPV 1 CLOSED for example.'
                status=MSG_BAD
            
        if 'PUMP' in msg:
            if msg.split()[2]=='HOME':
                return_msg='PUMP ' + msg.split()[1] + ' HOMED.'
                status=MSG_GOOD
                
                try:
                    if msg.split()[1]=='SEAWATER':
                        Seawater_pump.home()
                    if msg.split()[1]=='LYSIS':
                        Lysis_pump.home()
                    if msg.split()[1]=='PUSH':
                        Push_pump.home()
                    if msg.split()[1]=='PULL':
                        Pull_pump.home()
                    if msg.split()[1]=='DUMMY':
                        Dummy_pump.home()
                except:
                    return_msg='Critical error attempting to home Pump.'
                    
            else:
                if (int(msg.split()[2])>-1 and int(msg.split()[2])<15000):
                    if (int(msg.split()[3])>0 and int(msg.split()[3])<100):
                        if (int(msg.split()[1])>0 and int(msg.split()[1])<6): 
                            return_msg='PUMP ' + msg.split()[1] + ' activated for ' + msg.split()[2] + ' steps, ' + msg.split()[3] + ' cycles.'
                            status=MSG_GOOD
                        
                            try:
                                param1=int(msg.split()[2])
                                param2=int(msg.split()[3])
                                
                                if msg.split()[1]=='SEAWATER':
                                    print('Activating seawater pump.')
                                    Seawater_pump.dispense(  int(msg.split()[2]) , int(msg.split()[3])   )
                                if msg.split()[1]=='LYSIS':
                                    Lysis_pump.dispense(  int(msg.split()[2]) , int(msg.split()[3])   )
                                if msg.split()[1]=='PUSH':
                                    Push_pump.dispense(  int(msg.split()[2]) , int(msg.split()[3])   )
                                if msg.split()[1]=='PULL':
                                    Pull_pump.dispense(  int(msg.split()[2]) , int(msg.split()[3])   )
                                if msg.split()[1]=='DUMMY':
                                    Dummy_pump.dispense(  int(msg.split()[2]) , int(msg.split()[3])   )
                            except:
                                return_msg='Critical error attempting to dispense from Pump.'
                            

                        
            if not(status==MSG_GOOD):
                print('MSG is in fact BAD')
                return_msg='Error parsing PUMP command; PUMP 1 10000 3, for example.'
                status=MSG_BAD
            

        
        if 'TWV' in msg:
            if 'PORT E' in msg:
                threeway_valve.set('C')
                status=MSG_GOOD
                return_msg='TWV SET FOR PORT E'
            
            if 'PORT F' in msg:
                threeway_valve.set('D')
                status=MSG_GOOD
                return_msg='TWV SET FOR PORT F'
            
            if status != MSG_GOOD:
                return_msg='Error parsing TWV command; TWV PORT E for example.'
                status=MSG_BAD
        
        if 'COLLECT' in msg:
            if 'SEAWATER' in msg:
                status=MSG_GOOD
                feather_power.high()
                print('Waiting for Featherboard to boot up.')
                pyb.delay(3000)
                print('Sending start signal.')
                start_stop.high()
                print('Giving Featherboard moment to start flow sensor.')
                pyb.delay(1000)
                print('Pumping seawater.')
                start_stop.low()

                Seawater_pump.dispense(15000,100)

                print('Finished pumping seawater.')
                start_stop.high()
                pyb.delay(250)
                start_stop.low()

                print('Giving Featherboard time to properly shut down.')
                pyb.delay(3000)

                measured_flowrate= flowrate.read()
                return_msg='ADC_flowrate: ' + str(measured_flowrate)
                display_str='ADC_flowrate: ' + str(measured_flowrate) + '\n'
                print(display_str)
                pyb.delay(3000)
                print('Cutting power to the Featherboard.')
                pyb.delay(1000)
                feather_power.low() 
            
            if status != MSG_GOOD:
                return_msg='Error parsing COLLECT command; COLLECT SEAWATER for example.'
                status=MSG_BAD     
        
        print(return_msg)
        
        if status != NO_MSG:
            #for i in range(5):
            #    pyb.delay(5000)
            #    print('Processing long steps...')
                
            count=0
            while SENDING:
                msg=port.write(return_msg)
                if ('Error' in msg or 'Time' in msg or 'ACK' in msg):
                    count=count+1
                    if count>WRITE_ATTEMPTS:
                        print('Failed WRITE_ATTEMPTS at sending bytes.')
                        break
                else:
                    print('Acknowledgement received from Raspberry pi.')
                    break
                
                    
    #except:
    #    print('Unexpected error while attempting to receive instructions.')
    #    break