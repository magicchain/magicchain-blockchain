#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

from . import ethcontract

def scanDeposits(*, db, config):
    ethcontract.scanDeposits(db=db, config=config)

    # TODO: other deposit scanners if needed
