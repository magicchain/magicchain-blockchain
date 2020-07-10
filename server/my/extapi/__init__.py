#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

from . import ethcontract

def register(*, db, config, registry):
    ethcontract.register(db=db, config=config, registry=registry)

def customResultHandler(name):
    if name=="mint":
        def mintResultHandler(receipt, result):
            for logEntry in receipt["logs"]:
                if len(logEntry["topics"])>1 and logEntry["topics"][0]=="0xea630aa0f059e408d9549df47528546a0da45532fa05f28a90600a8617e3be1e":
                    result.update(tokenId=logEntry["topics"][1])
                    break
            return result

        return mintResultHandler

    return None
