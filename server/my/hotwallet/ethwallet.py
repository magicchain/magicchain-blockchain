#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

from .. import ethconfig
from .. import ethqueue


def isCoinNameAccepted(*, config, coin):
    coinDescription=ethconfig.findCoinDescription(config=config, coin=coin)
    if not coinDescription:
        return False

    if coinDescription.hotWallet is None:
        return False

    return True

def send(*, db, config, uuid, coin, amount, tokenId, recipient):
    coinDescription=ethconfig.findCoinDescription(config=config, coin=coin)
    assert coinDescription is not None

    # TODO: check balance first!


    queue=ethqueue.Queue(db=db, config=config)

    if coinDescription.type=="":
        queue.sendTransaction(
            uuid=uuid,
            chainid=coinDescription.chainid,
            sender=coinDescription.hotWallet,
            receiver=recipient,
            value=amount,
            data=b'')

    elif coinDescription.type=="ERC223":
        queue.sendTransaction(
            uuid=uuid,
            chainid=coinDescription.chainid,
            sender=coinDescription.hotWallet,
            receiver=coinDescription.contract,
            value=0,
            # transfer(address, uint256)
            data=b"\xa9\x05\x9c\xbb"+12*b'\0'+bytes.fromhex(receiver[2:])+amount.to_bytes(32, "big"))

    elif coinDescription.type=="ERC721":
        queue.sendTransaction(
            uuid=uuid,
            chainid=coinDescription.chainid,
            sender=coinDescription.hotWallet,
            receiver=coinDescription.contract,
            value=0,
            # safeTransferFrom(address, address, uint256)
            data=b"\x42\x84\x2e\x0e"+12*b'\0'+bytes.fromhex(coinDescription.hotWallet[2:])+12*b'\0'+bytes.fromhex(recipient[2:])+bytes.fromhex(tokenId[2:]))
