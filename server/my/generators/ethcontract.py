#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

from .. import ethconfig
from .. import ethqueue
from ..nodepool import *
import uuid

class DepositAddressGenerator:
    @staticmethod
    def isCoinNameAccepted(*, config, coin):
        return ethconfig.findCoinDescription(config=config, coin=coin) is not None

    def __init__(self, *, db, config, coin):
        self.db=db
        self.config=config
        self.coin=coin
        self.coinDescription=ethconfig.findCoinDescription(config=config, coin=coin)
        assert self.coinDescription is not None

    def generateAddressImmediately(self, userid):
        # Immediate address generation is not supported for ETH.
        return None

    def getExistingAddress(self, userid):
        return self.db.getExistingDepositAddress(coin=self.coinDescription.parentCoinSymbol, userid=userid)

    def addAddressRequest(self, userid):
        self.db.addDepositAddressRequest(
            coin=self.coinDescription.parentCoinSymbol,
            userid=userid)

    def generateAddress(self, userid):
        info=self.db.getDepositAddressRequest(coin=self.coin, userid=userid)
        assert info is not None
        assert info.status>0 # Pending

        queue=ethqueue.Queue(db=self.db, config=self.config)

        status=info.status
        txuuid=info.txuuid

        # Newborn address request
        if status==1:
            status=2
            txuuid=str(uuid.uuid4())

            self.db.updateDepositAddress(coin=self.coin, userid=userid, status=status, txuuid=txuuid)

        # There's txuuid, but there may be not be transaction request
        if status==2:
            if not queue.getTransaction(txuuid):
                queue.sendTransaction(
                    uuid=txuuid,
                    chainid=self.coinDescription.chainid,
                    sender=self.coinDescription.depositController,
                    receiver=self.coinDescription.depositContract,
                    value=0,
                    data=b"\x32\x33\x1f\xeb"+userid.to_bytes(32, "big"))

            status=3
            self.db.updateDepositAddress(coin=self.coin, userid=userid, status=status)

        # Transaction was issued, waiting for result
        if status==3:
            txinfo=queue.getTransaction(txuuid)
            assert txinfo is not None

            if txinfo.status==0:
                nodepool=NodePool(config=self.config)
                node=nodepool.connectToAnyNode(self.coinDescription.chainid)

                receipt=node.eth_getTransactionReceipt(txinfo.txhash)
                if receipt is not None:
                    r_userid, r_address=DepositAddressGenerator.__getUseridAndAddressFromReceipt(receipt)
                    if r_userid is None or r_userid!=userid:
                        self.db.updateDepositAddress(coin=self.coin, userid=userid, status=-13)
                    else:
                        self.db.updateDepositAddress(coin=self.coin, userid=userid, status=0, address=r_address)

            elif txinfo.status<0:
                # Transaction execution error, propagate it to 'addresses' table
                self.db.updateDepositAddress(uuid=info.txuuid, chainid=self.coinDescription.chainid, status=txinfo.status)

    @staticmethod
    def __getUseridAndAddressFromReceipt(receipt):
        if not isinstance(receipt, dict):
            return None, None

        if "logs" not in receipt or not isinstance(receipt["logs"], list):
            return None, None

        for logentry in receipt["logs"]:
            if not isinstance(logentry, dict):
                continue

            if "topics" not in logentry or logentry["topics"]!=["0xd3c75d3774b298f1efe8351f0635db8123b649572a5b810e96f5b97e11f43031"]:
                continue

            if "data" not in logentry or len(logentry["data"])!=130:
                continue

            data=logentry["data"]
            return int(data[2:66], 16), "0x"+data[90:130]

        return None, None
