#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

from . import ethcontract
from ..notify import *

def scanDeposits(*, db, config):
    ethcontract.scanDeposits(db=db, config=config)

    # TODO: other deposit scanners if needed

    notifier=Notifier(config=config)
    for depositInfo in db.getPendingDeposits():
        ok=notifier.sendData(
            "deposit",
            coin=depositInfo.coin,
            txid=depositInfo.txid,
            vout=depositInfo.vout,
            blockNumber=depositInfo.blockNumber,
            userid=depositInfo.userid,
            amount=depositInfo.amount,
            tokenId=depositInfo.tokenId)
        if ok is True:
            db.updateDeposit(coin=depositInfo.coin, txid=depositInfo.txid, vout=depositInfo.vout, notified=True)
