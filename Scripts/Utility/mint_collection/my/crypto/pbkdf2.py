#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj
# Implementation according to https://en.wikipedia.org/wiki/PBKDF2
# Test vectors as defined in RFC6070

import struct

def pbkdf2(password, salt, iterations, key_length, prf):
    block_number=0
    result=b''

    while len(result)<key_length:
        block_number+=1

        u=prf(password, salt+struct.pack('>L', block_number))
        r=list(u)
        for _ in range(1, iterations):
            un=prf(password, u)
            r=[ri^uni for (ri,uni) in zip(r, un)]
            u=un
        result+=bytes(r)

    return result[:key_length]

if __name__=="__main__":
    import hashlib
    import hmac

    prf=lambda key, data: hmac.new(key, data, hashlib.sha1).digest()

    assert pbkdf2(b"password", b"salt", 1, 20, prf)==bytes.fromhex("0c60c80f961f0e71f3a9b524af6012062fe037a6")
    assert pbkdf2(b"password", b"salt", 2, 20, prf)==bytes.fromhex("ea6c014dc72d6f8ccd1ed92ace1d41f0d8de8957")
    assert pbkdf2(b"password", b"salt", 4096, 20, prf)==bytes.fromhex("4b007901b765489abead49d926f721d065a429c1")
    assert pbkdf2(b"password", b"salt", 16777216, 20, prf)==bytes.fromhex("eefe3d61cd4da4e4e9945b3d6ba2158c2634e984")
    assert pbkdf2(b"passwordPASSWORDpassword", b"saltSALTsaltSALTsaltSALTsaltSALTsalt", 4096, 25, prf)==bytes.fromhex("3d2eec4fe41c849b80c8d83662c0e44a8b291a964cf2f07038")
    assert pbkdf2(b"pass\0word", b"sa\0lt", 4096, 16, prf)==bytes.fromhex("56fa6aa75548099dcc37d7f03425e0c3")
