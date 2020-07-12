#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

from .. import cgijsonrpc

class ListDeposits:
    def __init__(self, *, db):
        self.db=db

    def __call__(self, start=1, limit=25):
        return [d._asdict() for d in self.db.listDeposits(start, limit)]
