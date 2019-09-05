#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

# Both used for RFC6979 deterministic signatures
import hmac, hashlib

p=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
q=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx=0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy=0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8

def extgcd(a, b):
    x1=0
    y1=1
    x=1
    y=0
    while b!=0:
        q,r=divmod(a, b)
        x2=x-q*x1
        y2=y-q*y1
        a,b=b,r
        x,x1=x1,x2
        y,y1=y1,y2
    return a,x,y

def modinv(a, m):
    a%=m
    d,x,y=extgcd(a, m)
    if d==1:
        return (x+m)%m
    else:
        raise ZeroDivisionError("modular inverse doesn't exist")

def restoreY(x):
    global p

    a=pow(x, 3, p)+7
    if a>=p:
        a-=p
    if pow(a, (p-1)//2, p)!=1:
        raise ValueError("not a square residue")

    y=pow(a, (p+1)//4, p)

    return y

def addPoints(pt1, pt2):
    global p

    if pt1==(0, 0):
        return pt2
    if pt2==(0, 0):
        return pt1

    if pt1[0]==pt2[0] and (pt1[1]+pt2[1]) in (0, p):
        return (0, 0)

    if pt1==pt2:
        s=(3*pt1[0]*pt1[0]*modinv(2*pt1[1], p))%p
    else:
        s=((pt1[1]+p-pt2[1])*modinv(pt1[0]+p-pt2[0], p))%p

    x=(s*s+p-pt1[0]+p-pt2[0])%p
    y=(p-pt1[1]+s*(pt1[0]+p-x))%p

    return (x, y)

def mulPoint(pt, k):
    if k==0:
        return (0, 0)
    elif k==1:
        return pt

    res=(0, 0)
    while k!=0:
        if k%2==1:
            res=addPoints(res, pt)
        pt=addPoints(pt, pt)
        k>>=1

    return res

def makePublicKey(privateKey):
    # TODO: privkey must be bytes
    # TODO: result must be bytes (public key is some common format)
    return mulPoint((Gx, Gy), privateKey)

def rfc6979_bits2int(bits):
    if len(bits)>32:
        bits=bits[:32]
    if len(bits)<32:
        bits=(32-len(bits))*b'\x00'+bits

    return int.from_bytes(bits, "big")

def rfc6979_int2octets(x):
    return x.to_bytes(32, "big")

def rfc6979_bits2octets(bits):
    global q

    z1=rfc6979_bits2int(bits)
    z2=z1 if z1<q else (z1-q)
    return rfc6979_int2octets(z2)

def rfc6979_hmac(key, value):
    return hmac.new(key=key, msg=value, digestmod=hashlib.sha256).digest()

def rfc6979_genk(hash, privateKey):
    # 3.2.b
    V=32*b'\x01'
    # 3.2.c
    K=32*b'\x00'
    # 3.2.d
    K=rfc6979_hmac(K, V+b'\x00'+rfc6979_int2octets(privateKey)+rfc6979_bits2octets(hash))
    # 3.2.e
    V=rfc6979_hmac(K, V)
    # 3.2.f
    K=rfc6979_hmac(K, V+b'\x01'+rfc6979_int2octets(privateKey)+rfc6979_bits2octets(hash))
    # 3.2.g
    V=rfc6979_hmac(K, V)

    # 3.2.h
    while True:
        # 3.2.h.1
        T=b''
        # 3.2.h.2
        while len(T)<32:
            V=rfc6979_hmac(K, V)
            T=T+V

        # 3.2.h.3
        k=rfc6979_bits2int(T)
        if k>=1 and k<q:
            yield k

        K=rfc6979_hmac(K, V+b'\x00')
        V=rfc6979_hmac(K, V)

def makeSignature(hash, privateKey):
    global q

    h=rfc6979_bits2int(hash)%q

    for k in rfc6979_genk(hash, privateKey):
        rx,ry=mulPoint((Gx, Gy), k)
        r,overflow=(rx,0) if rx<q else (rx-q,2)
        if r==0:
            continue
        v=overflow+(ry%2)
        s=modinv(k, q)*(h+r*privateKey)%q
        if s==0:
            continue

        if q-s<s:
            s=q-s
            v^=1

        break

    return (r,s,v)

def recoverPublicKey(r, s, v, hash):
    global p, q

    h=rfc6979_bits2int(hash)%q

    rx=r if v<2 else r+q

    try:
        ry=restoreY(rx)
    except:
        return None

    if ry%2!=v%2:
        ry=p-ry if ry!=0 else 0

    try:
        r1=modinv(r, q)
    except:
        return None

    sR=mulPoint((rx, ry), s)
    hG=mulPoint((Gx, -Gy), h)

    return mulPoint(addPoints(sR, hG), r1)


if __name__=="__main__":
    privkey=0x0e5c7fb8a2d0f8d6113e0b0d6822681f66cf42cfa72dabf5ed49070fc374e331
    pubkey=makePublicKey(privkey)

    print("{0:x},{1:x}".format(*pubkey))

    r, s, v=makeSignature(hashlib.sha256(b"Hello").digest(), privkey)
    print("{0:x},{1:x},{2}".format(r, s, v))

    pk=recoverPublicKey(r, s, v, hashlib.sha256(b"Hello").digest())
    print("{0:x},{1:x}".format(*pk))
