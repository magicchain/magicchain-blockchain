#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj


class Queue:
    def __init__(self, *, db, config):
        self.db=db
        self.config=config

    def sendTransaction(self, *, uuid, chainid, sender, receiver, value, data):
        self.db.addPendingTransaction(
            uuid=uuid,
            chainid=chainid,
            sender=sender,
            receiver=receiver,
            value=value,
            data=data)

    def getTransaction(self, *, uuid, chainid):
        return self.db.getTransaction(uuid=uuid, chainid=chainid)
