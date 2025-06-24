def calc(data):
    sum = 0
    for i in data:
        sum = sum + i
        sum &= 0xFF
    # print(f"SUM: {format(sum,'x')}")
    sum = sum ^ 0xFF

    return data + sum.to_bytes(1, byteorder='big')
    

def check(data, key):
    sum = 0#key ^ 0xFF
    for i in data:
        sum = sum + i
        sum &= 0xFF
    # print(f"SUM: {format(sum,'x')}")
    sum = sum ^ 0xFF
    print(f"SUM == KEY: {sum} == {key}")
    return sum.to_bytes(len(key), byteorder='big') == key

def check_msg(msg, check_bytes=1):
    return check(msg[0:-check_bytes], msg[-check_bytes:])

if __name__ == "__main__":
    print(f"Running checksum demo")
    data = "Hello".encode()
    
    send = calc(data)

    print(f"DATA: {send}")
    l = len(send)
    ch = check(send[0:-1], send[-1:])

    print(f"CH: {ch}")

    ch_m = check_msg(send)
    print(f"ch_m: {ch_m}")

