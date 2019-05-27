#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

from .. import generators

class GetAddress:
    def __init__(self, *, db, config):
        self.db=db
        self.config=config

    def __call__(self, userid, coin):
        if not isinstance(userid, int):
            raise TypeError("userid argument must be an integer")

        address=generators.getAddress(db=self.db, config=self.config, userid=userid, coin=coin)
        if address is not None:
            res=dict(pending=False, userid=userid, coin=coin, address=address.address)
            res.update(address.extra)

            return res

        return dict(pending=True)
