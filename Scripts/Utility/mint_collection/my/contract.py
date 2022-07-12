#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

import os
import my


class Contract:
    def __init__(self, name, address = None, deploy_receipt = None):
        self.name           = name
        self.address        = address
        self.deploy_receipt = deploy_receipt

        abi_file = os.path.join(my.config.contracts.abi_files, name+".abi")
        abi = open(abi_file, "rt").read()

        self.w3contract = my.geth.eth.contract(abi=abi, address=address)

    def get_function_by_name(self, name):
        return self.w3contract.get_function_by_name(name)

    def get_function_by_selector(self, selector):
        return self.w3contract.get_function_by_selector(selector)
