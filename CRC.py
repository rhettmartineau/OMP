def crc8(datagram, initial_value):
    crc = initial_value
    for byte in datagram:
        # Iterate bits in byte
        byte=reverseBits(byte) #Sensirion goes MSB to LSB
        for _ in range(0, 8):
            if (crc >> 7) ^ (byte & 0x01):
                crc = ((crc << 1) ^ 0x31) & 0xFF #0x07
            else:
                crc = (crc << 1) & 0xFF
            # Shift to next bit
            byte = byte >> 1
    return crc

def reverseBits(n) : 
  pre=''
  length=8
  spacer=0
  binary_str='{0}{{:{1}>{2}}}'.format(pre, spacer, length).format(bin(n)[2:])
  rev_str = "".join(reversed(binary_str)) 
  return int(rev_str,2)  


