#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

import os
import json
import my
import my.crypto.secp256k1
import my.crypto.ethereum


class call_method(my.actions.action):
    @classmethod
    def make_action_id(cls, *, contract, method, caller_prv, value, args, **kwargs):
        def mangle_arg(arg):
            if isinstance(arg, bytes):
                return "0x"+arg.hex()
            return arg

        mangled_args=tuple((mangle_arg(arg) for arg in args))

        return super().make_action_id(contract.name,
                                      contract.address,
                                      method,
                                      caller_prv,
                                      value,
                                      *mangled_args,
                                      **kwargs)

    @classmethod
    def make_human_readable_name(cls, *, contract, method, caller_prv, value, args, **kwargs):
        if isinstance(method, str):
            return "{0}.{1}".format(contract.name, method)
        elif isinstance(method, int):
            return "{0}.{1:08x}".format(contract.name, method)
        elif isinstance(method, bytes):
            return "{0}.{1}".format(contract.name, method.hex())

    @staticmethod
    def format_result(result, *args, **kwargs):
        return json.loads(result)

    def __init__(self, *, contract, method, caller_prv, value, args, **kwargs):
        super().__init__()

        caller_pub = my.crypto.secp256k1.makePublicKey(bytes.fromhex(caller_prv[2:]))
        caller = my.crypto.ethereum.makeAddress(caller_pub)

        if isinstance(method, str):
            fn = contract.get_function_by_name(method)(*args)
        elif isinstance(method, (int, bytes)):
            fn = contract.get_function_by_selector(method)(*args)
        else:
            raise TypeError("Don't know how to interpret method specified by '{}'".format(type(method).__name__))

        tx = fn.buildTransaction({"from":  my.geth.toChecksumAddress(caller),
                                  "value": value,
                                  "gas":   my.geth.eth.getBlock("latest").gasLimit})

        self.tx = my.actions.create("transact",
                                    sender_prv = caller_prv,
                                    receiver   = contract.address,
                                    value      = value,
                                    gas_price  = tx.get("gasPrice") or tx.get("maxFeePerGas"),
                                    gas_limit  = None,
                                    payload    = tx["data"],
                                    **kwargs)

    def idle(self):
        if self.tx.is_finished():
            if not self.is_finished():
                self.set_result(self.tx.get_raw_result())

        else:
            self.tx.idle()
