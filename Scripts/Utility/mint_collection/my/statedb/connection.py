#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

import sqlite3
from . import cache
from . import ethqueue


class Connection:
    def __init__(self, filename):
        self.db=sqlite3.connect(filename)

        self.db.executescript("""CREATE TABLE IF NOT EXISTS action_cache
(
  action_id TEXT NOT NULL,
  action_result TEXT,
  PRIMARY KEY(action_id)
);
CREATE TABLE IF NOT EXISTS ethqueue
(
  request_id TEXT NOT NULL,
  status INTEGER NOT NULL,
  sender TEXT NOT NULL,
  receiver TEXT,
  value TEXT NOT NULL,
  gas_price INTEGER UNSIGNED,
  gas_limit INTEGER UNSIGNED,
  nonce INTEGER UNSIGNED,
  payload TEXT NOT NULL,
  txhash TEXT,
  receipt TEXT,
  create_timestamp INTEGER UNSIGNED NOT NULL,
  send_timestamp INTEGER UNSIGNED,
  fee_increment_timestamp INTEGER UNSIGNED,
  next_check_timestamp INTEGER UNSIGNED,
  PRIMARY KEY(request_id)
);""")

        self.cache=cache.Cache(self.db)
        self.ethqueue=ethqueue.ETHQueue(self.db)
