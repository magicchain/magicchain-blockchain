#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

from .. import cgijsonrpc

class EstimateFee:
    def __init__(self, registry):
        self.registry=registry

    def __call__(self, requestname, requestparams):
        try:
            methodHandler=self.registry[requestname]
            estimateFee=getattr(methodHandler, "estimateFee")
        except (KeyError, AttributeError):
            raise cgijsonrpc.JsonRPCException(-1001, "Unknown request name")

        if isinstance(requestparams, list):
            return estimateFee(*requestparams)
        elif isinstance(requestparams, dict):
            return estimateFee(**requestparams)
        else:
            raise TypeError
