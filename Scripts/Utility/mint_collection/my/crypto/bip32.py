# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

from . import base58
from . import secp256k1
#import base58
#import secp256k1
import hashlib
import hmac
import struct

xpub=b"\x04\x88\xB2\x1E"
xprv=b"\x04\x88\xAD\xE4"
tpub=b"\x04\x35\x87\xCF"
tprv=b"\x04\x35\x83\x94"


def getKeyFingerprint(key):
    if isinstance(key, bytes) and len(key)==33:
        return hashlib.new("rmd160", hashlib.new("sha256", key).digest()).digest()[:4]
    elif isinstance(key, bytes) and len(key)==65:
        return getKeyFingerprint(secp256k1.compressPublicKey(key))
    else:
        return getKeyFingerprint(getPublicKey(key))

def isExtendedPublicKey(key):
    return base58.base58_decode(key)[:4] in (xpub, tpub)

def isExtendedPrivateKey(key):
    return base58.base58_decode(key)[:4] in (xprv, tprv)

def deriveExtendedPublicKey(parentKey, index):
    if isinstance(index, str):
        if isExtendedPrivateKey(parentKey):
            return getExtendedPublicKey(deriveExtendedPrivateKey(parentKey, index))

        path=index.split('/')

        if path[0]=='m':
            del path[0]

        for i in path:
            if i.endswith("'"):
                raise ValueError("Invalid derivation index")
            else:
                i=int(i)
            parentKey=deriveExtendedPublicKey(parentKey, i)

        return parentKey

    if not (0<=index<2**32):
        raise ValueError("Invalid derivation index")

    parentKeyBin=base58.base58_decode_checksum(parentKey)
    if len(parentKeyBin)!=78:
        raise ValueError("Invalid extended key length")

    parentPrefix=parentKeyBin[:4]

    if parentPrefix not in (xpub, xprv, tpub, tprv):
        raise ValueError("Invalid extended key prefix")

    parentDepth=parentKeyBin[4]
    if parentDepth==255:
        raise ValueError("Maximum derivation depth reached")

    parentIsPublic=parentPrefix in (xpub, tpub)
    isTestnet=parentPrefix in (tpub, tprv)

    if parentIsPublic and index>=2**31:
        raise ValueError("Invalid derivation index")

    if parentIsPublic:
        parentPublicKey=parentKeyBin[45:]
    else:
        parentPublicKey=secp256k1.makeCompressedPublicKey(parentKeyBin[46:])

    fingerprint=hashlib.new("rmd160", hashlib.new("sha256", parentPublicKey).digest()).digest()[:4]

    if index>=2**31:
        I=hmac.new(parentKeyBin[13:45], b"\0"+parentKeyBin[46:]+struct.pack(">L", index), hashlib.sha512).digest()
    else:
        I=hmac.new(parentKeyBin[13:45], parentPublicKey+struct.pack(">L", index), hashlib.sha512).digest()

    childPublicKey=secp256k1.modifyPublicKey(parentPublicKey, I[0:32])
    childChainCode=I[32:64]

    return base58.base58_encode_checksum(
        (tpub if isTestnet else xpub)+
        bytes((parentDepth+1,))+
        fingerprint+
        struct.pack(">L", index)+
        childChainCode+
        childPublicKey)

def deriveExtendedPrivateKey(parentPrivateKey, index):
    if isinstance(index, str):
        path=index.split('/')

        if path[0]=='m':
            del path[0]

        for i in path:
            if i.endswith("'"):
                i=2**31+int(i[:-1])
            else:
                i=int(i)
            parentPrivateKey=deriveExtendedPrivateKey(parentPrivateKey, i)

        return parentPrivateKey

    if not (0<=index<2**32):
        raise ValueError("Invalid derivation index")

    parentKeyBin=base58.base58_decode_checksum(parentPrivateKey)
    if len(parentKeyBin)!=78:
        raise ValueError("Invalid extended key length")

    parentPrefix=parentKeyBin[:4]
    if parentPrefix not in (xprv, tprv):
        raise ValueError("Invalid extended key prefix")

    parentDepth=parentKeyBin[4]
    if parentDepth==255:
        raise ValueError("Maximum derivation depth reached")

    isTestnet=(parentPrefix==tprv)

    parentPublicKey=secp256k1.makeCompressedPublicKey(parentKeyBin[46:])
    fingerprint=hashlib.new("rmd160", hashlib.new("sha256", parentPublicKey).digest()).digest()[:4]

    if index>=2**31:
        I=hmac.new(parentKeyBin[13:45], b"\0"+parentKeyBin[46:]+struct.pack(">L", index), hashlib.sha512).digest()
    else:
        I=hmac.new(parentKeyBin[13:45], parentPublicKey+struct.pack(">L", index), hashlib.sha512).digest()

    childPrivateKey=secp256k1.modifyPrivateKey(parentKeyBin[46:], I[0:32])
    childChainCode=I[32:64]

    return base58.base58_encode_checksum(
        (tprv if isTestnet else xprv)+
        bytes((parentDepth+1,))+
        fingerprint+
        struct.pack(">L", index)+
        childChainCode+
        bytes((0,))+
        childPrivateKey)

def derivePublicKey(parentKey, index):
    return getPublicKey(deriveExtendedPublicKey(parentKey, index))

def derivePrivateKey(parentPrivateKey, index):
    return getPrivateKey(deriveExtendedPrivateKey(parentPrivateKey, index))

def getExtendedPublicKey(extendedKey):
    extendedKeyBin=base58.base58_decode_checksum(extendedKey)
    if len(extendedKeyBin)!=78:
        raise ValueError("Invalid extended key length")

    prefix=extendedKeyBin[:4]

    if prefix in (xpub, tpub):
        return extendedKey
    elif prefix in (xprv, tprv):
        isTestnet=(prefix==tprv)
        publicKey=secp256k1.makeCompressedPublicKey(extendedKeyBin[46:])
        return base58.base58_encode_checksum(
            (tpub if isTestnet else xpub)+
            extendedKeyBin[4:45]+
            publicKey)
    else:
        raise ValueError("Invalid extended key prefix")

def getPublicKey(extendedKey):
    return base58.base58_decode(getExtendedPublicKey(extendedKey))[45:78]

def getPrivateKey(extendedKey):
    extendedKeyBin=base58.base58_decode_checksum(extendedKey)
    if len(extendedKeyBin)!=78:
        raise ValueError("Invalid extended key length")

    prefix=extendedKeyBin[:4]
    if prefix not in (xprv, tprv):
        raise ValueError("Invalid extended key prefix")

    return extendedKeyBin[46:78]

def generateMasterKeyFromSeed(seed, testnet = False):
    I=hmac.new(b"Bitcoin seed", seed, hashlib.sha512).digest()

    masterKey=I[0:32]
    masterChainCode=I[32:64]

    return base58.base58_encode_checksum(
        (tprv if testnet else xprv)+
        b"\x00"+
        b"\x00\x00\x00\x00"+
        b"\x00\x00\x00\x00"+
        masterChainCode+
        b"\x00"+
        masterKey)

if __name__=="__main__":
    assert deriveExtendedPublicKey("xprv9s21ZrQH143K3QTDL4LXw2F7HEK3wJUD2nW2nRk4stbPy6cq3jPPqjiChkVvvNKmPGJxWUtg6LnF5kejMRNNU3TGtRBeJgk33yuGBxrMPHi", 2**31)=="xpub68Gmy5EdvgibQVfPdqkBBCHxA5htiqg55crXYuXoQRKfDBFA1WEjWgP6LHhwBZeNK1VTsfTFUHCdrfp1bgwQ9xv5ski8PX9rL2dZXvgGDnw"
    assert deriveExtendedPrivateKey("xprv9s21ZrQH143K3QTDL4LXw2F7HEK3wJUD2nW2nRk4stbPy6cq3jPPqjiChkVvvNKmPGJxWUtg6LnF5kejMRNNU3TGtRBeJgk33yuGBxrMPHi", 2**31)=="xprv9uHRZZhk6KAJC1avXpDAp4MDc3sQKNxDiPvvkX8Br5ngLNv1TxvUxt4cV1rGL5hj6KCesnDYUhd7oWgT11eZG7XnxHrnYeSvkzY7d2bhkJ7"
    assert deriveExtendedPublicKey("xpub68Gmy5EdvgibQVfPdqkBBCHxA5htiqg55crXYuXoQRKfDBFA1WEjWgP6LHhwBZeNK1VTsfTFUHCdrfp1bgwQ9xv5ski8PX9rL2dZXvgGDnw", 1)=="xpub6ASuArnXKPbfEwhqN6e3mwBcDTgzisQN1wXN9BJcM47sSikHjJf3UFHKkNAWbWMiGj7Wf5uMash7SyYq527Hqck2AxYysAA7xmALppuCkwQ"
    assert deriveExtendedPublicKey("xprv9uHRZZhk6KAJC1avXpDAp4MDc3sQKNxDiPvvkX8Br5ngLNv1TxvUxt4cV1rGL5hj6KCesnDYUhd7oWgT11eZG7XnxHrnYeSvkzY7d2bhkJ7", 1)=="xpub6ASuArnXKPbfEwhqN6e3mwBcDTgzisQN1wXN9BJcM47sSikHjJf3UFHKkNAWbWMiGj7Wf5uMash7SyYq527Hqck2AxYysAA7xmALppuCkwQ"
    assert deriveExtendedPrivateKey("xprv9uHRZZhk6KAJC1avXpDAp4MDc3sQKNxDiPvvkX8Br5ngLNv1TxvUxt4cV1rGL5hj6KCesnDYUhd7oWgT11eZG7XnxHrnYeSvkzY7d2bhkJ7", 1)=="xprv9wTYmMFdV23N2TdNG573QoEsfRrWKQgWeibmLntzniatZvR9BmLnvSxqu53Kw1UmYPxLgboyZQaXwTCg8MSY3H2EU4pWcQDnRnrVA1xe8fs"

    assert getExtendedPublicKey("xpub661MyMwAqRbcFtXgS5sYJABqqG9YLmC4Q1Rdap9gSE8NqtwybGhePY2gZ29ESFjqJoCu1Rupje8YtGqsefD265TMg7usUDFdp6W1EGMcet8")=="xpub661MyMwAqRbcFtXgS5sYJABqqG9YLmC4Q1Rdap9gSE8NqtwybGhePY2gZ29ESFjqJoCu1Rupje8YtGqsefD265TMg7usUDFdp6W1EGMcet8"
    assert getExtendedPublicKey("xprv9s21ZrQH143K3QTDL4LXw2F7HEK3wJUD2nW2nRk4stbPy6cq3jPPqjiChkVvvNKmPGJxWUtg6LnF5kejMRNNU3TGtRBeJgk33yuGBxrMPHi")=="xpub661MyMwAqRbcFtXgS5sYJABqqG9YLmC4Q1Rdap9gSE8NqtwybGhePY2gZ29ESFjqJoCu1Rupje8YtGqsefD265TMg7usUDFdp6W1EGMcet8"

    assert generateMasterKeyFromSeed(bytes.fromhex("000102030405060708090a0b0c0d0e0f"))=="xprv9s21ZrQH143K3QTDL4LXw2F7HEK3wJUD2nW2nRk4stbPy6cq3jPPqjiChkVvvNKmPGJxWUtg6LnF5kejMRNNU3TGtRBeJgk33yuGBxrMPHi"
    assert generateMasterKeyFromSeed(bytes.fromhex("fffcf9f6f3f0edeae7e4e1dedbd8d5d2cfccc9c6c3c0bdbab7b4b1aeaba8a5a29f9c999693908d8a8784817e7b7875726f6c696663605d5a5754514e4b484542"))=="xprv9s21ZrQH143K31xYSDQpPDxsXRTUcvj2iNHm5NUtrGiGG5e2DtALGdso3pGz6ssrdK4PFmM8NSpSBHNqPqm55Qn3LqFtT2emdEXVYsCzC2U"
    assert generateMasterKeyFromSeed(bytes.fromhex("4b381541583be4423346c643850da4b320e46a87ae3d2a4e6da11eba819cd4acba45d239319ac14f863b8d5ab5a0d0c64d2e8a1e7d1457df2e5a3c51c73235be"))=="xprv9s21ZrQH143K25QhxbucbDDuQ4naNntJRi4KUfWT7xo4EKsHt2QJDu7KXp1A3u7Bi1j8ph3EGsZ9Xvz9dGuVrtHHs7pXeTzjuxBrCmmhgC6"
    assert getExtendedPublicKey("xprv9s21ZrQH143K25QhxbucbDDuQ4naNntJRi4KUfWT7xo4EKsHt2QJDu7KXp1A3u7Bi1j8ph3EGsZ9Xvz9dGuVrtHHs7pXeTzjuxBrCmmhgC6")=="xpub661MyMwAqRbcEZVB4dScxMAdx6d4nFc9nvyvH3v4gJL378CSRZiYmhRoP7mBy6gSPSCYk6SzXPTf3ND1cZAceL7SfJ1Z3GC8vBgp2epUt13"
    assert deriveExtendedPublicKey("xprv9s21ZrQH143K25QhxbucbDDuQ4naNntJRi4KUfWT7xo4EKsHt2QJDu7KXp1A3u7Bi1j8ph3EGsZ9Xvz9dGuVrtHHs7pXeTzjuxBrCmmhgC6", 2**31)=="xpub68NZiKmJWnxxS6aaHmn81bvJeTESw724CRDs6HbuccFQN9Ku14VQrADWgqbhhTHBaohPX4CjNLf9fq9MYo6oDaPPLPxSb7gwQN3ih19Zm4Y"
    assert deriveExtendedPrivateKey("xprv9s21ZrQH143K25QhxbucbDDuQ4naNntJRi4KUfWT7xo4EKsHt2QJDu7KXp1A3u7Bi1j8ph3EGsZ9Xvz9dGuVrtHHs7pXeTzjuxBrCmmhgC6", 2**31)=="xprv9uPDJpEQgRQfDcW7BkF7eTya6RPxXeJCqCJGHuCJ4GiRVLzkTXBAJMu2qaMWPrS7AANYqdq6vcBcBUdJCVVFceUvJFjaPdGZ2y9WACViL4L"
    assert getExtendedPublicKey("xprv9uPDJpEQgRQfDcW7BkF7eTya6RPxXeJCqCJGHuCJ4GiRVLzkTXBAJMu2qaMWPrS7AANYqdq6vcBcBUdJCVVFceUvJFjaPdGZ2y9WACViL4L")=="xpub68NZiKmJWnxxS6aaHmn81bvJeTESw724CRDs6HbuccFQN9Ku14VQrADWgqbhhTHBaohPX4CjNLf9fq9MYo6oDaPPLPxSb7gwQN3ih19Zm4Y"

    print("If you see it then all tests have passed")
