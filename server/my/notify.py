#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

import requests


class Notifier:
    def __init__(self, *, config):
        self.url=config["notify-url"]

    def sendNotification(self, methodName, **kwargs):
        requests.post(self.url, json={"jsonrpc": "2.0", "method": methodName, "params": kwargs})
