#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

from .. import hotwallet
from .. import cgijsonrpc

class Send:
    def __init__(self, *, db, config):
        self.db=db
        self.config=config

    def __call__(self, uuid, coin, amount, tokenId, recipient, **kwargs):
        try:
            hotwallet.send(
                db=self.db,
                config=self.config,
                uuid=uuid,
                coin=coin,
                amount=int(amount, 0),
                tokenId=tokenId,
                recipient=recipient,
                **kwargs)
            return None
        except:
            raise cgijsonrpc.JsonRPCException(-1001, "Duplicate UUID")

        # TODO: raise "invalid coin" error
