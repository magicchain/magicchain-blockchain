#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

class getTxStatus:
    def __init__(self, *, db):
        self.db=db

    def __call__(self, uuid):
        tx=self.db.getTransaction(uuid)
        if tx is None:
            return None
        elif tx.status>0:
            return dict(uuid=uuid, confirmed=False, pending=True, error=None)
        elif tx.status==0:
            return dict(uuid=uuid, confirmed=True, pending=False, error=None, txhash=tx.txhash)
        else:
            return dict(uuid=uuid, confirmed=False, pendiing=False, error=status)
