#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

from .call_method import *
from .action import *


class call_method_mint(call_method):
    @classmethod
    def make_action_id(cls, *, contract, caller_prv, address, content, fee):
        return action.make_action_id(contract.name,
                                     contract.address,
                                     "mint",
                                     caller_prv,
                                     address,
                                     content,
                                     fee)

    @classmethod
    def make_human_readable_name(cls, *, contract, caller_prv, address, content, fee):
        return f"MintMe.mint(address={address}, content=/ipfs/{content})"

    def __init__(self, contract, caller_prv, address, content, fee):
        super().__init__(contract      = contract,
                         method        = "mint",
                         caller_prv    = caller_prv,
                         value         = fee,
                         args          = (address, content))
