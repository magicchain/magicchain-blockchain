#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

from .. import ethconfig
from .. import ethqueue
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
            if not queue.getTransaction(uuid=txuuid, chainid=self.coinDescription.chainid):
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
            txinfo=queue.getTransaction(uuid=txuuid, chainid=self.coinDescription.chainid)
            assert txinfo is not None


            if txinfo.status==0:
                # TODO: get tx receipt

                # TODO: extract address from log

                # TODO: alternatively, it's possible to call eth_call to get address from the contract storage

                # TODO: notify



                pass

            elif txinfo.status<0:
                # Transaction execution error, propagate it to 'addresses' table
                self.db.updateDepositAddress(uuid=info.txuuid, chainid=self.coinDescription.chainid, status=txinfo.status)

                # TODO: notify about error
