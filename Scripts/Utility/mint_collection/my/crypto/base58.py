# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

import hashlib

def base58_decode(s):
    res=[]
    zeroes=0
    left=True
    n=0
    for c in s:
        if c=='1' and left:
            zeroes+=1
        else:
            left=False
            n=n*58+"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz".index(c)
    while n!=0:
        n,r=divmod(n, 256)
        res.append(r)

    return bytes((zeroes*[0])+res[::-1])

def base58_encode(b):
    res=[]
    zeroes=0
    left=True
    n=0
    for c in b:
        if c==0 and left:
            zeroes+=1
        else:
            left=False
            n=n*256+c
    while n!=0:
        n,r=divmod(n, 58)
        res.append("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"[r])

    return (zeroes*"1")+("".join(res[::-1]))

def base58_decode_checksum(s):
    b=base58_decode(s)

    if len(b)<4:
        raise ValueError("Checksummed base58 string is too short")

    chksum=hashlib.new("sha256", hashlib.new("sha256", b[:-4]).digest()).digest()[:4]
    if b[-4:]!=chksum:
        raise ValueError("Invalid base58 checksum")

    return b[:-4]

def base58_encode_checksum(b):
    chksum=hashlib.new("sha256", hashlib.new("sha256", b).digest()).digest()[:4]
    return base58_encode(b+chksum)

if __name__=="__main__":
    assert base58_decode("1Maniaccv5vSQVuwrmRtfazhf2WsTxaAuV")==b"\x00\xe1\xc6\x67\xaa\xe7\xe7\x10\x94\x2d\xf8\xd2\x3a\x67\x4c\xfb\x75\xbb\x94\x45\xeb\x00\x00\x00\x00"
    assert base58_encode(b"\x00\xe1\xc6\x67\xaa\xe7\xe7\x10\x94\x2d\xf8\xd2\x3a\x67\x4c\xfb\x75\xbb\x94\x45\xeb\x00\x00\x00\x00")=="1Maniaccv5vSQVuwrmRtfazhf2WsTxaAuV"
    assert base58_encode_checksum(b"\x00\xe1\xc6\x67\xaa\xe7\xe7\x10\x94\x2d\xf8\xd2\x3a\x67\x4c\xfb\x75\xbb\x94\x45\xeb")=="1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD"
