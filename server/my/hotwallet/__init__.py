#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

from . import ethwallet

def send(*, db, config, uuid, coin, amount, tokenId, recipient, **kwargs):
    if ethwallet.isCoinNameAccepted(config=config, coin=coin):
        return ethwallet.send(db=db, config=config, uuid=uuid, coin=coin, amount=amount, tokenId=tokenId, recipient=recipient)

    # TODO: raise "unsupported coin" exception
