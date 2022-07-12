#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj


class Cache:
    def __init__(self, db):
        self.db=db

    def find_result(self, action_id):
        r=self.db.execute("SELECT action_result FROM action_cache WHERE action_id=?;", (action_id,)).fetchone()
        if r is None:
            raise KeyError()

        return r[0]

    def store_result(self, action_id, action_result):
        self.db.execute("INSERT INTO action_cache VALUES (?, ?);", (action_id, action_result))
        self.db.commit()
