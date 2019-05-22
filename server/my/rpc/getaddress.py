#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

from .. import generators

class getAddress:
    def __init__(self, *, db, config):
        self.db=db
        self.config=config

    def __call__(self, userid, coin):
        if not isinstance(userid, int):
            raise TypeError("userid argument must be an integer")

        # TODO: "address" may (must?) be an object with additional fields ("message" for NEM)

        address=generators.getAddress(db=self.db, config=self.config, userid=userid, coin=coin)
        if address is not None:
            return {"pending": False, "userid": userid, "coin": coin, "address": address}

        return {"pending": True}
