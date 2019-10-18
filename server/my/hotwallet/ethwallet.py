#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

from .. import ethconfig
from .. import ethqueue
from .. import ethfee
import re


def isCoinNameAccepted(*, config, coin):
    coinDescription=ethconfig.findCoinDescription(config=config, coin=coin)
    if not coinDescription:
        return False

    if coinDescription.hotWallet is None:
        return False

    return True

def __makeTxArgs(*, config, coin, amount, tokenId, recipient):
    coinDescription=ethconfig.findCoinDescription(config=config, coin=coin)
    assert coinDescription is not None

    if not isinstance(recipient, str) or re.fullmatch("0x[0-9a-fA-F]{40}", recipient) is None:
        raise ValueError("Invalid recipient address {}".format(recipient))

    if coinDescription.type=="":
        try:
            amount=int(amount, 0)
        except ValueError:
            raise ValueError("Invalid amount")

        if tokenId is not None:
            raise ValueError("TokenID is not applicable to coin {}".format(coin))

        return dict(
            chainid=coinDescription.chainid,
            sender=coinDescription.hotWallet,
            receiver=recipient,
            value=amount,
            data=b'')

    elif coinDescription.type=="ERC223":
        try:
            amount=int(amount, 0)
        except ValueError:
            raise ValueError("Invalid amount")

        if tokenId is not None:
            raise ValueError("TokenID is not applicable to coin {}".format(coin))

        return dict(
            chainid=coinDescription.chainid,
            sender=coinDescription.hotWallet,
            receiver=coinDescription.contract,
            value=0,
            # transfer(address, uint256)
            data=b"\xa9\x05\x9c\xbb"+12*b'\0'+bytes.fromhex(recipient[2:])+amount.to_bytes(32, "big"))

    elif coinDescription.type=="ERC721":
        if amount is not None:
            raise ValueError("Amount is not applicable to coin {}".format(coin))

        if not isinstance(tokenId, str) or re.fullmatch("0x[0-9a-fA-F]{64}", tokenId) is None:
            raise ValueError("Invalid TokenID format")

        return dict(
            chainid=coinDescription.chainid,
            sender=coinDescription.hotWallet,
            receiver=coinDescription.contract,
            value=0,
            # safeTransferFrom(address, address, uint256)
            data=b"\x42\x84\x2e\x0e"+12*b'\0'+bytes.fromhex(coinDescription.hotWallet[2:])+12*b'\0'+bytes.fromhex(recipient[2:])+bytes.fromhex(tokenId[2:]))


def send(*, db, config, uuid, coin, amount, tokenId, recipient):
    queue=ethqueue.Queue(db=db, config=config)
    queue.sendTransaction(
        uuid=uuid,
        **__makeTxArgs(
            config=config,
            coin=coin,
            amount=amount,
            tokenId=tokenId,
            recipient=recipient))

def estimateFee(*, config, coin, amount, tokenId, recipient):
    return ethfee.estimateFee(
        config=config,
        **__makeTxArgs(
            config=config,
            coin=coin,
            amount=amount,
            tokenId=tokenId,
            recipient=recipient))
