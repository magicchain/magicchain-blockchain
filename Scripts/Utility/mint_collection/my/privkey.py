#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

import getpass
import my.crypto.bip39
import my.crypto.bip32
import my.crypto.ethereum
import my.crypto.secp256k1
import my.crypto.eip55


def get_private_key_and_address(cfgstr):
    if cfgstr.startswith("m/"):
        # The contracts' owner is specified as BIP32 derivation path. So, it's
        # needed to ask for passphrase and derive owner's private key
        passphrase = getpass.getpass("Master passphrase: ")
        root_xprv  = my.crypto.bip39.generateMasterKeyFromPassphrase(passphrase)
        child_xprv = my.crypto.bip32.deriveExtendedPrivateKey(root_xprv, cfgstr)
        child_prv  = my.crypto.bip32.getPrivateKey(child_xprv)

    elif cfgstr.startswith("0x"):
        # The contract's owner is specified as hex private key with 0x prefix
        child_prv = bytes.fromhex(cfgstr[2:])

    else:
        # The contract's owner is specified as hex private key without 0x prefix
        child_prv = bytes.fromhex(cfgstr)

    child_address = my.crypto.ethereum.makeAddress(my.crypto.secp256k1.makePublicKey(child_prv))
    child_address = my.crypto.eip55.makeChecksummedAddress(child_address)
    child_prv     = "0x"+child_prv.hex()

    return (child_prv, child_address)
