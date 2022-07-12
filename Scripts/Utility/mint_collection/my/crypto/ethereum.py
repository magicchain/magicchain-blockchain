# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

from . import keccak as keccaklib
from . import secp256k1

def keccak(data):
    return keccaklib.keccak(data, 1088, 256, 0x01)

def makeAddress(pubkey):
    if len(pubkey)==33:
        pubkey=secp256k1.uncompressPublicKey(pubkey)

    if len(pubkey) in (64, 65):
        return "0x"+keccak(pubkey[-64:])[-20:].hex()

    raise ValueError("Invalid public key length")
