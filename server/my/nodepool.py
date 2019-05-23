#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

import jsonrpclib


class NodePool:
    def __init__(self, *, config):
        self.config=config["nodes"]

    def connectToAnyNode(self, chainid):
        for n in self.config:
            if n["chainId"]==chainid:
                return jsonrpclib.Server("http://{0}:{1}".format(n["address"], n["port"]))
        return None
