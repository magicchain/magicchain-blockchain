#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

from .nodepool import *
import time


class Queue:
    def __init__(self, *, db, config):
        self.db=db
        self.config=config

    def sendTransaction(self, *, uuid, chainid, sender, receiver, value, data):
        self.db.addPendingTransaction(
            uuid=uuid,
            chainid=chainid,
            sender=sender,
            receiver=receiver,
            value=value,
            data=data)

    def getTransaction(self, uuid):
        return self.db.getTransaction(uuid)

    def processTransaction(self, uuid):
        info=self.db.getTransaction(uuid)
        assert info is not None
        assert info.status>0 # Pending

        nodepool=NodePool(config=self.config)
        node=nodepool.connectToAnyNode(info.chainid)

        if info.status==1:

            # estimate gas
            txobject={}
            txobject["from"]=info.sender
            txobject["to"]=info.receiver

            #txobject["gasPrice"]=
            txobject["gas"]="0x{:x}".format(1000000)
            txobject["data"]="0x"+info.data.hex()

            try:
                txobject["gas"]=node.eth_estimateGas(txobject)
                txobject["gas"]=node.eth_estimateGas(txobject)
            except:
                pass

            # TODO: keep passwords somewhere
            # TODO+: sing transactions
            node.personal_unlockAccount(info.sender, "1")

            # send tx
            # TODO: use raw transaction instead
            self.db.updateTransaction(uuid=uuid, status=2, sendTime=int(time.time()), gasLimit=txobject["gas"])
            txhash=node.eth_sendTransaction(txobject)

            # TODO: store txhash into db
            self.db.updateTransaction(uuid=uuid, status=3, txhash=txhash)
            # TODO: (-32000, "insufficient funds for gas * price + value")
            # TODO: handle None or 0x000...00

        elif info.status==3:
            try:
                receipt=node.eth_getTransactionReceipt(info.txhash)
            except:
                receipt=None

            if receipt is None:
                # TODO: too long? send again

                pass
            else:
                topBlock=int(node.eth_blockNumber(), 16)
                confirmations=topBlock-int(receipt["blockNumber"], 16)+1

                if confirmations>=4:
                    if int(receipt["status"], 16)==1:
                        self.db.updateTransaction(uuid=uuid, status=0)
                    else:
                        self.db.updateTransaction(uuid=uuid, status=-12)
