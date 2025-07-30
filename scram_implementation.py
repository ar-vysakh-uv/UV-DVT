## Author - Dhananjay

def xor_lut(input_data):
    # Byte 7:0 to be XORed with 0xC3
    re_xored_bytes = bytes([byte ^ 0xC3 for byte in input_data])
    print("1st LUT output :", ' '.join(f'{b:02X}' for b in re_xored_bytes))
    return re_xored_bytes

def and_lut(input_data):
    # Byte 7:0 to be ANDed with 0xEC
    re_xored_bytes = bytes([byte & 0xEC for byte in input_data])
    print("2nd LUT output :", ' '.join(f'{b:02X}' for b in re_xored_bytes))
    return re_xored_bytes

def rs_lut(input_data):
    # Byte 7:0 to be RIGHT SHIFT by 2
    rightshift_bytes = bytes([byte >> 2 for byte in input_data])
    print("3rd LUT output :", ' '.join(f'{b:02X}' for b in rightshift_bytes))
    return rightshift_bytes

def rs_and_xor_lut(input_data):
    # Byte 7:0 to be RIGHT SHIFT by 2 and XOR with Byte 5 of the packet
    ref_byte = input_data[5]
    rightshift_bytes = bytes([(byte >> 2) ^ ref_byte for byte in input_data])
    print("4th LUT output :", ' '.join(f'{b:02X}' for b in rightshift_bytes))
    return rightshift_bytes

def even_and_xor_lut(input_data):
    # Even Bytes of the packet to be XORed with Byte 3
    ref_byte = input_data[3]
    re_xored_bytes = bytes(b ^ ref_byte if i % 2 == 0 else b for i, b in enumerate(input_data))
    print("5th LUT output :", ' '.join(f'{b:02X}' for b in re_xored_bytes))
    return re_xored_bytes

def interchange_lut(input_data):
    # Exchange the Byte 3 with Byte 6 and Byte 2 with Byte 7
    data = list(input_data)
    # Swap B3 and B6 → index 2 and 5
    data[3], data[6] = data[6], data[3]
    # Swap B2 and B7 → index 1 and 6
    data[2], data[7] = data[7], data[2]
    print("6th LUT output :", ' '.join(f'{b:02X}' for b in data))
    return data

def compliment_lut(input_data):
    # Compliment all the packet data
    compliment = [~b & 0xFF for b in input_data]
    print("7th LUT output :", ' '.join(f'{b:02X}' for b in compliment))
    return compliment

def xor_bytes(data1: list, data2: list) -> bytes:
    # XOR'ing all the bytes again with the Key
    if len(data1) != 8 or len(data2) != 8:
        raise ValueError("Both inputs must be exactly 8 elements long.")
    return bytes([x ^ k for x, k in zip(data1, data2)])

def dexor_data(input_data):
    Key = [0x3A, 0x7F, 0xC4, 0xE9, 0x5B, 0xA2, 0x18, 0xD7]
    # Recover original by XOR'ing with the original key
    original_bytes = xor_bytes(input_data, Key)
    print("Recovered Original Hex :", ' '.join(f'{b:02X}' for b in original_bytes))
    return original_bytes

def rexor_data(input_data):
    Key = [0x3A, 0x7F, 0xC4, 0xE9, 0x5B, 0xA2, 0x18, 0xD7]
    # XOR original again with predefined to get back xored_data
    encoded_bytes = xor_bytes(list(input_data), Key)
    print("Challenge Response :", ' '.join(f'{b:02X}' for b in encoded_bytes))
    return encoded_bytes

def scram_decode(data):

    if data[0] == 0x3A:
        recovered_data = dexor_data(data)
        LUT_operation = xor_lut(recovered_data)
        response_out = rexor_data(LUT_operation)
        return response_out
    
    if data[0] == 0x3B:
        recovered_data = dexor_data(data)
        LUT_operation = and_lut(recovered_data)
        response_out = rexor_data(LUT_operation)
        return response_out

    if data[0] == 0x38:
        recovered_data = dexor_data(data)
        LUT_operation = rs_lut(recovered_data)
        response_out = rexor_data(LUT_operation)
        return response_out

    if data[0] == 0x39:
        recovered_data = dexor_data(data)
        LUT_operation = rs_and_xor_lut(recovered_data)
        response_out = rexor_data(LUT_operation)
        return response_out

    if data[0] == 0x3E:
        recovered_data = dexor_data(data)
        LUT_operation = even_and_xor_lut(recovered_data)
        response_out = rexor_data(LUT_operation)
        return response_out

    if data[0] == 0x3F:
        recovered_data = dexor_data(data)
        LUT_operation = interchange_lut(recovered_data)
        response_out = rexor_data(LUT_operation)
        return response_out

    if data[0] == 0x3C:
        recovered_data = dexor_data(data)
        LUT_operation = compliment_lut(recovered_data)
        response_out = rexor_data(LUT_operation)
        return response_out
    
    else:
        print("No Response generated.... Auth Challenge is not valid ")
        return None