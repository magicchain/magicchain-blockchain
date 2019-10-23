#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

from .nodepool import *
from . import ethconfig
from .cgijsonrpc import JsonRPCException


def estimateFee(*, config, chainid, sender, receiver, value, data):
    nodepool=NodePool(config=config)
    node=nodepool.connectToAnyNode(chainid)
    if not node:
        raise JsonRPCException(-1002, "No live ethereum node found")

    # Get current gas price
    gasPrice=int(node.eth_gasPrice(), 16)

    # Prepare tx struct to call eth_estimateGas
    txobject={}
    txobject["from"]=sender
    txobject["to"]=receiver
    txobject["value"]="0x{:x}".format(value)
    txobject["data"]="0x"+data.hex()
    txobject["gasPrice"]="0x{:x}".format(gasPrice)
    txobject["gas"]="0x{:x}".format(1000000)

    txobject["gas"]=node.eth_estimateGas(txobject)
    txobject["gas"]=node.eth_estimateGas(txobject)

    gas=int(txobject["gas"], 16)

    symbol=ethconfig.getPrimaryCoinSymbol(config=config, chainid=chainid)
    assert symbol is not None

    return {symbol: "{:d}".format(gas*gasPrice)}
