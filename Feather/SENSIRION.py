# This contains a class definition for the Sensiron SLF3S-1300F Liquid Flow Sensor
import machine, pyb, CRC
import micropython
from array import array
import ustruct
micropython.alloc_emergency_exception_buf(100)

class SLF3S():
    """
    FlowSensor class creates an interface to Sensirion SLF3S-1300F Liquid Flow Sensor
    Supported methods:
    
    """
    ADDRESS=0x08
    START=b'\x36\x08'
    STOP=b'\x3F\xF9'
    RESET=b'\x06'
    RESETADDRESS=0x00
    
    FLOWRATE_SCALE_FACTOR=500 #min/ml
    TEMPERATURE_SCALE_FACTOR=200 #/C
        
    def __init__(self):
      self._i2c = machine.I2C(scl=machine.Pin('A4'), sda=machine.Pin('A5'))
      self._i2c.init(scl=machine.Pin('A4'), sda=machine.Pin('A5'), freq=168000)
      pyb.delay(250)
      self._i2c.start()
      self._i2c.write(b'\x00\x06')
      self._i2c.stop()
      
      print('Soft reset cycled.')
      pyb.delay(500)
           
    def start (self):
      self._i2c.start()
      self._i2c.write(b'\x10\x36\x08')
      self._i2c.stop()
      print('Entered into continuous measurement mode.')
      pyb.delay(150)
      
    def stop (self):
      self._i2c.writeto(SLF3S.ADDRESS, SLF3S.STOP)
      print('Exited from continuous measurement mode.')
      
    def reset (self):
      self._i2c.writeto(SLF3S.ADDRESS, SLF3S.RESET)
      print('Device soft reset.')
         
    def read (self):
      data_out=[0]*4
      self.bytes_in=array("B", [0]*9)
      self._i2c.start()
      self._i2c.write(b'\x11')
      self._i2c.readinto(self.bytes_in)
      self._i2c.stop()
      flow_raw=ustruct.unpack('>h', self.bytes_in[0:2])[0]
      
      self.flow=flow_raw/self.FLOWRATE_SCALE_FACTOR
      temp_raw=ustruct.unpack('>h', self.bytes_in[3:5])[0]
      self.temp=temp_raw/self.TEMPERATURE_SCALE_FACTOR
      self.signaling_flags=ustruct.unpack('>h', self.bytes_in[6:8])[0]
      flow_Checksum=self.bytes_in[2]
      temp_Checksum=self.bytes_in[5]
      signaling_flags_Checksum=self.bytes_in[8]

      flow_calc_Checksum=CRC.crc8(self.bytes_in[0:2], 0xFF)
      temp_calc_Checksum=CRC.crc8(self.bytes_in[3:5], 0xFF)
      flag_calc_Checksum=CRC.crc8(self.bytes_in[6:8], 0xFF)
           
      if flow_calc_Checksum==flow_Checksum:
        data_out[0]=self.flow
      else:
        data_out[0]=-999
        data_out[3]=-1
      
      if temp_calc_Checksum==temp_Checksum:
        data_out[1]=self.temp
      else:
        data_out[1]=-999
        data_out[3]=-1
        
      if flag_calc_Checksum==signaling_flags_Checksum:
        data_out[2]=1
      else:
        data_out[2]=-999
        data_out[3]=-1
        
      return data_out
      











