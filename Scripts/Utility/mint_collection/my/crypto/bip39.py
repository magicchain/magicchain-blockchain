# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

from . import pbkdf2
from . import bip32
import hashlib
import hmac


def generateMasterKeyFromPassphrase(passphrase, testnet = False):
    passphrase=passphrase.encode("utf8")

    prf=lambda key, msg: hmac.new(key, msg, hashlib.sha512).digest()
    masterseed=pbkdf2.pbkdf2(passphrase, b"mnemonic", 2048, 64, prf)

    return bip32.generateMasterKeyFromSeed(masterseed, testnet)
