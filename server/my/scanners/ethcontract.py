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

        elif coinDescription.type=="ERC223":
            scanERC223Deposits(
                coin=coinDescription.symbol,
                node=node,
                tokenContract=coinDescription.contract,
                depositContract=coinDescription.depositContract,
                db=db)

        elif coinDescription.type=="ERC721":
            scanERC721Deposits(
                coin=coinDescription.symbol,
                node=node,
                tokenContract=coinDescription.contract,
                depositContract=coinDescription.depositContract,
                db=db)

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
            tokenId=None,
            tokenContent=None)

    db.setLastScannedBlock(coin=coin, blockNumber=toBlock)

def scanERC223Deposits(*, coin, node, tokenContract, depositContract, db):
    fromBlock=(db.getLastScannedBlock(coin=coin) or 0)+1
    toBlock=int(node.eth_blockNumber(), 16)-4

    filter={}
    filter["fromBlock"]="0x{:x}".format(fromBlock)
    filter["toBlock"]="0x{:x}".format(toBlock)
    filter["address"]=depositContract
    filter["topics"]=["0x7ca4363cd84b59fc2751c5d5025b81010bcfcdca51a8cc9dbce140e303444ee1", "0x"+12*"00"+tokenContract[2:]]

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
            tokenId=None,
            tokenContent=None)

    db.setLastScannedBlock(coin=coin, blockNumber=toBlock)

def scanERC721Deposits(*, coin, node, tokenContract, depositContract, db):
    fromBlock=(db.getLastScannedBlock(coin=coin) or 0)+1
    toBlock=int(node.eth_blockNumber(), 16)-4

    TOPIC1="0x331f29737013eaa09945e5a312c0ae07eca0ef4b486254221f441809d78c2a0e"
    TOPIC2="0x0cd7d376fec15305db85abcc745038e1d1fc429906c75a23f6ab8003a11994e2"

    filter={}
    filter["fromBlock"]="0x{:x}".format(fromBlock)
    filter["toBlock"]="0x{:x}".format(toBlock)
    filter["address"]=depositContract
    filter["topics"]=[[TOPIC1, TOPIC2], "0x"+12*"00"+tokenContract[2:]]

    logs=node.eth_getLogs(filter)
    for logEntry in logs:
        if "data" not in logEntry:
            continue

        if logEntry["topics"][0]==TOPIC1:
            # Generic ERC721 deposit
            if len(logEntry["data"])!=130:
                continue

            userid=int(logEntry["data"][2:66], 16)
            tokenid="0x"+logEntry["data"][66:130]

            db.addNewDeposit(
                coin=coin,
                txid=logEntry["transactionHash"],
                vout=int(logEntry["logIndex"], 16),
                blockNumber=int(logEntry["blockNumber"], 16),
                userid=userid,
                amount=None,
                tokenId=tokenid,
                tokenContent=None)

        elif logEntry["topics"][0]==TOPIC2:
            # MCI-specific ERC721 deposit
            if len(logEntry["data"])!=450:
                continue

            userid=int(logEntry["data"][2:66], 16)
            tokenid="0x"+logEntry["data"][66:130]
            tokenContent=["0x"+logEntry["data"][130+i*64:130+(i+1)*64] for i in range(5)]

            db.addNewDeposit(
                coin=coin,
                txid=logEntry["transactionHash"],
                vout=int(logEntry["logIndex"], 16),
                blockNumber=int(logEntry["blockNumber"], 16),
                userid=userid,
                amount=None,
                tokenId=tokenid,
                tokenContent=tokenContent)

    db.setLastScannedBlock(coin=coin, blockNumber=toBlock)
