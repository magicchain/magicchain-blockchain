#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

import time
import collections


Request=collections.namedtuple(
    "Request",
    [
        "request_id",
        "status",
        "sender",
        "receiver",
        "value",
        "gas_price",
        "gas_limit",
        "nonce",
        "payload",
        "txhash",
        "receipt",
        "create_timestamp",
        "send_timestamp",
        "fee_increment_timestamp",
        "next_check_timestamp"
    ])

class ETHQueue:
    def __init__(self, db):
        self.db=db

    def add_new_request(self, request_id, sender, receiver, value, gas_price, gas_limit, payload):
        self.db.execute("INSERT OR IGNORE INTO ethqueue "
                        "VALUES (?, 1, ?, ?, ?, ?, ?, NULL, ?, NULL, NULL, ?, NULL, NULL, 0);",
                        (request_id, sender, receiver, value, gas_price, gas_limit, payload, round(1000*time.time())))
        self.db.commit()

    def get_request(self, request_id):
        r=self.db.execute("SELECT * FROM ethqueue WHERE "
                          "request_id=? AND "
                          "next_check_timestamp IS NOT NULL AND "
                          "next_check_timestamp<=?;",
                          (request_id, round(1000*time.time()))).fetchone()
        if r is None:
            return None

        return Request(*r[0:4], int(r[4]), *r[5:])

    def update_request(self, request_id, **kwargs):
        sets = []
        for key in kwargs.keys():
            if key in ("status", "sender", "receiver", "value", "gas_price", "gas_limit", "nonce", "payload", "txhash", "receipt", "create_timestamp", "send_timestamp", "fee_increment_timestamp", "next_check_timestamp"):
                sets.append("{name}=:{name}".format(name=key))

        if len(sets)==0:
            return

        self.db.execute("UPDATE ethqueue SET "+",".join(sets)+" WHERE request_id=:request_id;",
                        dict(request_id=request_id, **kwargs))
        self.db.commit()

    def find_highest_nonce(self, sender):
        r=self.db.execute("SELECT MAX(nonce) FROM ethqueue WHERE sender=? AND nonce IS NOT NULL;", (sender,)).fetchone()
        return r[0]

    def retry_after(self, request_id, seconds):
        self.update_request(request_id, next_check_timestamp = round(1000*(time.time()+seconds)))
