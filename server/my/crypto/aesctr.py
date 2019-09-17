#! /usr/bin/env python3

from . import aes


def encrypt(iv, key, plaintext):
    assert len(iv)==aes.BLOCK_SIZE

    ciphertext=[]
    pos=0
    enc=aes.AES(key)
    while pos<len(plaintext):
        cnt=len(plaintext)-pos
        if cnt>aes.BLOCK_SIZE:
            cnt=aes.BLOCK_SIZE

        mask=enc.encrypt(iv)
        for i in range(cnt):
            ciphertext.append(plaintext[pos+i]^mask[i])

        carry=1
        l=list(iv)
        for i in range(len(l)-1, -1, -1):
            l[i]+=carry
            l[i],carry=l[i]&255,int(l[i]==256)
            if not carry:
                break
        iv=bytes(l)

        pos+=cnt

    return bytes(ciphertext)

def decrypt(iv, key, cyphertext):
    return encrypt(iv, key, cyphertext)

if __name__=="__main__":
    def test(keystr, ivstr, instr, outstr):
        import binascii

        k=binascii.a2b_hex(keystr)
        iv=binascii.a2b_hex(ivstr)
        p=binascii.a2b_hex(instr)
        c=binascii.a2b_hex(outstr)

        assert encrypt(iv, k, p)==c
        assert decrypt(iv, k, c)==p

    # NIST test vectors
    test("2b7e151628aed2a6abf7158809cf4f3c", "f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff", "6bc1bee22e409f96e93d7e117393172aae2d8a571e03ac9c9eb76fac45af8e5130c81c46a35ce411e5fbc1191a0a52eff69f2445df4f9b17ad2b417be66c3710", "874d6191b620e3261bef6864990db6ce9806f66b7970fdff8617187bb9fffdff5ae4df3edbd5d35e5b4f09020db03eab1e031dda2fbe03d1792170a0f3009cee")
    test("8e73b0f7da0e6452c810f32b809079e562f8ead2522c6b7b", "f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff", "6bc1bee22e409f96e93d7e117393172aae2d8a571e03ac9c9eb76fac45af8e5130c81c46a35ce411e5fbc1191a0a52eff69f2445df4f9b17ad2b417be66c3710", "1abc932417521ca24f2b0459fe7e6e0b090339ec0aa6faefd5ccc2c6f4ce8e941e36b26bd1ebc670d1bd1d665620abf74f78a7f6d29809585a97daec58c6b050")
    test("603deb1015ca71be2b73aef0857d77811f352c073b6108d72d9810a30914dff4", "f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff", "6bc1bee22e409f96e93d7e117393172aae2d8a571e03ac9c9eb76fac45af8e5130c81c46a35ce411e5fbc1191a0a52eff69f2445df4f9b17ad2b417be66c3710", "601ec313775789a5b7a7f504bbf3d228f443e3ca4d62b59aca84e990cacaf5c52b0930daa23de94ce87017ba2d84988ddfc9c58db67aada613c2dd08457941a6")
