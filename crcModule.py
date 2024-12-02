
import random

def getCRC(data, divisor_key):
    position = len(divisor_key)                 # Position of bit to be dropped | determined by number of bits to XOR
    dividend = data + '0'*(position-1)          # Append n bits to data

    dividend_slice = dividend[0:position]       # Slice dividend (for XORing in correct length)

    while position < len(dividend):
        if dividend_slice[0] == '1': dividend_slice = xor(dividend_slice, divisor_key)[1:]+dividend[position]   # If divedend's leftmost is 1 -> XOR with key (omit leftmost answer) and dropdown bit using [position] 
        else: dividend_slice = xor(dividend_slice, '0'*len(divisor_key))[1:]+dividend[position]                 # If divedend's leftmost is 0 -> XOR with zeros (omit leftmost answer) and dropdown bit using [position]
        position += 1                                                                                           # Move position until end is reached (position = dividend length) and prevent out-of-bounds error

    if dividend_slice[0] == '1': dividend_slice = xor(dividend_slice, divisor_key)[1:]                          # If divedend's leftmost is 1 -> XOR with key (omit leftmost answer) witout drop-down 
    else: dividend_slice = xor(dividend_slice, '0'*len(divisor_key))[1:]                                        # If divedend's leftmost is 0 -> XOR with zeros (omit leftmost answer) witout drop-down
    crc = dividend_slice                                                                                        # This final "slice" iteration is the CRC
    return crc

def xor(a, b):
    #pad the shorter one with zeroes to match
    max_len = max(len(a), len(b))               # Get the longest length
    a = a.zfill(max_len)                        # Pad 0s to the left of a until max length is reached
    b = b.zfill(max_len)                        # Pad 0s to the left of b until max length is reached
    
    ans = ''
    for i in range(max_len):
        ans = ans + str(int(a[i])^int(b[i]))    # Loop through their length and keep appending XOR [^] result to ans
    return ans                                  # Return XOR result (a string of binary)

def corruptMessage(binary_str):
    corruptChance = 0.05                # 5% chance to be corrupted during transmission
    if random.random() < corruptChance:         # if the generated number is [0.00 - 0.04] or 5/100
        corruptedDecimalRep = int(binary_str, 2) + 1     # Convert to decimal and add 1
        binary_str = bin(corruptedDecimalRep)[2:]           #convert back to binary
    return binary_str

    
def toBinary(str):
    bytes = str.encode()                                    # Turn string into bytes
    binary = ''.join(format(byte, '08b') for byte in bytes) # I opted for 8 bits here instead of 7 bits for UTF-8 (with padding if needed)
    return binary                                           # Return a string of binary

def toText(binary_str):
    binary_bytes = [binary_str[i:i+8] for i in range(0, len(binary_str), 8)]    #slice the binary string into chunks of 8
    int_bytes = [int(byte, 2) for byte in binary_bytes]                         #take each byte (binary form) and convert to an integer (specifying base-2) 
    return bytes(int_bytes).decode()                                            #convert list of bytes (integer form) into a bytes object which could then be decoded and returned

def getCRCMsg(message, key):
    binaryMsg = toBinary(message)   # converting message to binary string represenration
    binaryCRC = getCRC(binaryMsg, key)  # get the CRC
    finalMsg = binaryMsg+binaryCRC
    return finalMsg