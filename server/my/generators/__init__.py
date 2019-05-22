#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

from . import ethcontract


def getAddress(*, db, config, userid, coin):
    """Should be used from RPC handler. It returns immediately and doesn't
    perform potentially long operations.
    """

    if not isinstance(userid, int):
        raise TypeError("userid argument must be an integer")

    g=chooseGenerator(db=db, config=config, coin=coin)

    address=g.generateAddressImmediately(userid)
    if address is not None:
        return address

    address=g.getExistingAddress(userid)
    if address is not None:
        return address

    g.addAddressRequest(userid)

    return None

def generateAddress(*, db, config, userid, coin):
    if not isinstance(userid, int):
        raise TypeError("userid argument must be an integer")

    g=chooseGenerator(db=db, config=config, coin=coin)

    return g.generateAddress(userid)

def chooseGenerator(*, db, config, coin):
    if ethcontract.DepositAddressGenerator.isCoinNameAccepted(config=config, coin=coin):
        return ethcontract.DepositAddressGenerator(db=db, config=config, coin=coin)

    # Other coins here...

    else:
        raise ValueError("Unsupported coin name {0}".format(coin))
