#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

import os
import sys
import web3
from . import actions
from . import privkey
from . import config as configlib
from . import statedb as statedblib
from .contract import Contract


config=configlib.load(os.path.splitext(sys.argv[0])[0]+".conf")
statedb=statedblib.Connection(config.state_database.filename)

if hasattr(config.geth, "ipc"):
    geth = web3.Web3(web3.Web3.IPCProvider(config.geth.ipc, request_kwargs={"timeout": 60}))
elif hasattr(config.geth, "rpc"):
    geth = web3.Web3(web3.Web3.HTTPProvider(config.geth.rpc, request_kwargs={"timeout": 60}))

if geth.eth.chain_id in (1337, 80001): # devnet?
    geth.middleware_onion.inject(web3.middleware.geth_poa_middleware, layer=0)
