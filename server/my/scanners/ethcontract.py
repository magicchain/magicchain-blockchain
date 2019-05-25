#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

from .. import ethconfig
from ..nodepool import *

def scanDeposits(*, db, config):
    nodepool=NodePool(config=config)

    for coinDescription in ethconfig.listCoinDescriptions(config):
        if coinDescription.depositContract is None:
            continue

        node=nodepool.connectToAnyNode(coinDescription.chainid)
        if node is None:
            continue

        if coinDescription.type=="":
            scanEthereumDeposits(
                coin=coinDescription.symbol,
                node=node,
                depositContract=coinDescription.depositContract,
                db=db)

        # TODO: erc-223
        
        # TODO: erc-721


def scanEthereumDeposits(*, coin, node, depositContract, db):
    fromBlock=(db.getLastScannedBlock(coin=coin) or 0)+1
    toBlock=int(node.eth_blockNumber(), 16)-4

    filter={}
    filter["fromBlock"]="0x{:x}".format(fromBlock)
    filter["toBlock"]="0x{:x}".format(toBlock)
    filter["address"]=depositContract
    filter["topics"]=["0xa04639d57c39e9ecf6bd06db2a5999f9b34681857c07ab9d986b998c893171ad"]

    logs=node.eth_getLogs(filter)
    for logEntry in logs:
        if "data" not in logEntry or len(logEntry["data"])!=130:
            continue

        userid=int(logEntry["data"][2:66], 16)
        amount=int(logEntry["data"][66:130], 16)

        db.addNewDeposit(
            coin=coin,
            txid=logEntry["transactionHash"],
            vout=int(logEntry["logIndex"], 16),
            blockNumber=int(logEntry["blockNumber"], 16),
            userid=userid,
            amount="0x{:x}".format(amount),
            tokenId=None)

    db.setLastScannedBlock(coin=coin, blockNumber=toBlock)
