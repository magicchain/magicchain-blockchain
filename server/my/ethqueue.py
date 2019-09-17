#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

from .nodepool import *
from .ethbuildtx import *
import time
import traceback


class Queue:
    STATUS_FINISHED=0
    STATUS_PENDING=1
    STATUS_NONCE_SET=2
    STATUS_GAS_PRICE_SET=3
    STATUS_GAS_LIMIT_SET=4
    STATUS_SENT=5

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

        # TODO: check balance as ealier as possible (before acquiring nonce)

        # TODO: check presence of private key. Suspend request if the key doesn't exist


        if info.status==self.STATUS_PENDING:
            # Choose nonce for new transaction
            try:
                netNonce=int(node.eth_getTransactionCount(info.sender, "latest"), 16)
            except:
                return

            lastNonce=self.db.findHighestNonce(sender=info.sender)
            if lastNonce is None:
                nonce=netNonce
            else:
                nonce=max(lastNonce+1, netNonce)

            info=info._replace(nonce=nonce, status=self.STATUS_NONCE_SET)
            self.db.updateTransaction(uuid=uuid, status=info.status, nonce=info.nonce)

            # Don't return, fall through instead

        if info.status==self.STATUS_NONCE_SET:
            # Get current gas price
            try:
                gasPrice=int(node.eth_gasPrice(), 16)
            except:
                return

            info=info._replace(gasPrice=gasPrice, status=self.STATUS_GAS_PRICE_SET)
            self.db.updateTransaction(uuid=uuid, status=info.status, gasPrice=info.gasPrice)

            # Don't return, fall through instead

        if info.status in (self.STATUS_GAS_PRICE_SET, self.STATUS_GAS_LIMIT_SET):
            txobject={}
            txobject["from"]=info.sender
            txobject["to"]=info.receiver
            txobject["value"]="0x{:x}".format(info.value)
            txobject["data"]="0x"+info.data.hex()
            txobject["nonce"]="0x{:x}".format(info.nonce)
            txobject["gasPrice"]="0x{:x}".format(info.gasPrice)

            if info.status==self.STATUS_GAS_PRICE_SET:
                # estimate gas
                txobject["gas"]="0x{:x}".format(1000000)

                try:
                    txobject["gas"]=node.eth_estimateGas(txobject)
                    txobject["gas"]=node.eth_estimateGas(txobject)
                except:
                    return

                info=info._replace(gasLimit=int(txobject["gas"], 16), status=self.STATUS_GAS_LIMIT_SET)
                self.db.updateTransaction(uuid=uuid, status=info.status, gasLimit=info.gasLimit)

            if info.status==self.STATUS_GAS_LIMIT_SET:
                # send
                txobject["gas"]="0x{:x}".format(info.gasLimit)

                privateKey=self.db.getPrivateKey(info.sender)

                rawtx="0x"+build(privateKey=privateKey, **txobject).hex()
                txhash=node.eth_sendRawTransaction(rawtx)

                info=info._replace(txhash=txhash, status=self.STATUS_SENT)
                self.db.updateTransaction(uuid=uuid, status=info.status, sendTime=int(time.time()), txhash=info.txhash)

        if info.status==self.STATUS_SENT:
            # Wait for tx receipt

            try:
                topBlock=int(node.eth_blockNumber(), 16)
            except:
                # TODO: node temporary failure, wait for 1 minute
                return

            try:
                receipt=node.eth_getTransactionReceipt(info.txhash)
            except:
                receipt=None

            if receipt is None:
                # TODO: too long? send again

                pass
            else:
                confirmations=topBlock-int(receipt["blockNumber"], 16)+1

                if confirmations>=4:
                    if int(receipt["status"], 16)==1:
                        self.db.updateTransaction(uuid=uuid, status=self.STATUS_FINISHED)
                    else:
                        self.db.updateTransaction(uuid=uuid, status=-12)
