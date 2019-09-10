#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

from . import rlp
from . import keccak
from . import secp256k1

def build(*, privateKey, nonce, gasPrice, gas, to, value, data, **kwargs):
    if isinstance(nonce, str) and nonce.startswith("0x"):
        nonce=int(nonce, 16)
    if isinstance(gasPrice, str) and gasPrice.startswith("0x"):
        gasPrice=int(gasPrice, 16)
    if isinstance(gas, str) and gas.startswith("0x"):
        gas=int(gas, 16)
    if isinstance(to, str) and to.startswith("0x") and len(to)==42:
        to=bytes.fromhex(to[2:])
    if isinstance(value, str) and value.startswith("0x"):
        value=int(value, 16)
    if isinstance(data, str) and data.startswith("0x"):
        data=bytes.fromhex(data[2:])

    h=keccak.keccak(rlp.dumpb([nonce, gasPrice, gas, to, value, data]), 1088, 256, 0x01)

    r,s,v=secp256k1.makeSignature(h, privateKey)

    return rlp.dumpb([
        nonce,
        gasPrice,
        gas,
        to,
        value,
        data,
        b'\x1b' if v==0 else b'\x1c',
        r,
        s])
