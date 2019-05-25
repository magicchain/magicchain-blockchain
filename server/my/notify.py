#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

import jsonrpclib


class Notifier:
    def __init__(self, *, config):
        self.serverProxy=jsonrpclib.Server(config["notify-url"])

    def sendNotification(self, methodName, **kwargs):
        try:
            getattr(self.serverProxy._notify, methodName)(**kwargs)
        except:
            pass

    def sendData(self, methodName, **kwargs):
        try:
            return getattr(self.serverProxy, methodName)(**kwargs)
        except:
            return None
