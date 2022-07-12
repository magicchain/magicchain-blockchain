# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

from .ethereum import keccak

def makeChecksummedAddress(address):
    chksum=keccak(address[2:].encode("latin1")).hex()
    return "0x"+"".join((c.upper() if int(chksum[i], 16)>=8 else c for i,c in enumerate(address[2:])))
