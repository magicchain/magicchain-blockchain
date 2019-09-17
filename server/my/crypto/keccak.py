#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# Based on code by Guido Bertoni, Joan Daemen, Michaël Peeters,
# Gilles Van Assche and Ronny Van Keer


def ROL64(a, offset):
    return ((1<<64)-1)&((a<<offset)^(a>>(64-offset)))

def LFSR86540(LFSR):
    r=(LFSR&0x01)!=0
    if LFSR&0x80!=0:
        LFSR=(LFSR<<1)^0x171
    else:
        LFSR=(LFSR<<1)
    return r,LFSR

def keccak_permute(state):
    LFSRstate=0x01
    for round in range(24):
        C=[state[x]^state[x+5]^state[x+10]^state[x+15]^state[x+20] for x in range(5)]
        for x in range(5):
            D=C[(x+4)%5]^ROL64(C[(x+1)%5], 1)
            for y in range(5):
                state[x+5*y]^=D

        x,y=1,0
        current=state[x+5*y]
        for t in range(24):
            r=((t+1)*(t+2)//2)%64
            x,y=y,(2*x+3*y)%5

            state[x+5*y],current=ROL64(current, r),state[x+5*y]

        for y in range(5):
            temp=[state[x+5*y] for x in range(5)]
            for x in range(5):
                state[x+5*y]=temp[x]^((((1<<64)-1)^temp[(x+1)%5])&temp[(x+2)%5])

        for j in range(7):
            r,LFSRstate=LFSR86540(LFSRstate)
            if r:
                state[0]^=1<<((1<<j)-1)

    return state

def keccak(data, rate, hashbitlen, suffix):
    state=25*[0]
    pos=0
    rate//=8
    hashsize=hashbitlen//8

    for c in data:
        state[pos//8]^=c<<(8*(pos%8))
        pos+=1
        if pos==rate:
            state=keccak_permute(state)
            pos=0

    state[pos//8]^=suffix<<(8*(pos%8))
    if (suffix&0x80)!=0 and pos==rate-1:
        state=keccak_permute(state)
    state[(rate-1)//8]^=0x80<<(8*((rate-1)%8))
    state=keccak_permute(state)

    h=[]
    while hashsize>0:
        bs=min(hashsize, rate)
        hashsize-=bs
        h.extend((0xFF&(state[pos//8]>>(8*(pos%8))) for pos in range(bs)))
        state=keccak_permute(state)

    return bytes(h)


if __name__=="__main__":
    import binascii
    print(binascii.b2a_hex(keccak(b"abc", 1088, 256, 0x06)))
    print(binascii.b2a_hex(keccak(b"", 1088, 256, 0x06)))
    print(binascii.b2a_hex(keccak(b"abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq", 1088, 256, 0x06)))
    print(binascii.b2a_hex(keccak(b"abcdefghbcdefghicdefghijdefghijkefghijklfghijklmghijklmnhijklmnoijklmnopjklmnopqklmnopqrlmnopqrsmnopqrstnopqrstu", 1088, 256, 0x06)))
