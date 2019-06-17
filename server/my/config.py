#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

import os, json


class Config:
    def __init__(self, filename=None):
        if filename is None:
            filename=Config.getDefaultFileName()

        self.data=json.load(open(filename, "rt"))

    def __getitem__(self, key):
        return self.data[key]

    def get(self, key, default=None):
        return self.data.get(key, default)

    @staticmethod
    def getDefaultFileName():
        try:
            return os.environ["MC_PAYMENT_CONFIG"]
        except KeyError:
            filename=os.path.expanduser("~/.magicchain/payment.conf")
            if os.access(filename, os.R_OK):
                return filename
            else:
                return "/etc/magicchain/payment.conf"
