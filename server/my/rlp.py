#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

def dumpb(data):
    if type(data)==bytes:
        if len(data)==1 and data[0]<=0x7F:
            return data
        elif len(data)<=55:
            return bytes([0x80+len(data)])+data
        else:
            lenlen=(len(data).bit_length()+7)//8
            return bytes([0xB7+lenlen])+len(data).to_bytes(lenlen, "big")+data
    elif type(data)==str:
        return dumpb(data.encode("utf8"))
    elif type(data)==int:
        return dumpb(data.to_bytes((data.bit_length()+7)//8, "big"))
    elif type(data)==list:
        payload=b"".join(map(dumpb, data))
        if len(payload)<=55:
            return bytes([0xC0+len(payload)])+payload
        else:
            lenlen=(len(payload).bit_length()+7)//8
            return bytes([0xF7+lenlen])+len(payload).to_bytes(lenlen, "big")+payload

# Not needed:
# def loadb(data):
#     ...

if __name__=="__main__":
    def printhex(data):
        print(" ".join(("{0:02X}".format(x) for x in data)))

    printhex(dumpb("dog"))
    printhex(dumpb(["cat", "dog"]))
    printhex(dumpb(""))
    printhex(dumpb([]))
    printhex(dumpb(b"\x0F"))
    printhex(dumpb(b"\x04\x00"))
    printhex(dumpb([[], [[]], [[], [[]]]]))
    printhex(dumpb("Lorem ipsum dolor sit amet, consectetur adipisicing elit"))
