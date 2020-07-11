#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

from .. import ethconfig
from .. import ethqueue
from .. import ethfee
from ..nodepool import *
from .. import cgijsonrpc
from .. import extapi

def makeTransactionData(selector, argtypes, args):
    if not isinstance(args, list):
        raise TypeError('"args" argument must be an array')

    if len(args)!=len(argtypes):
        raise TypeError("{0} argument(s) expected, {1} given".format(len(argtypes), len(args)))

    txdata=bytes.fromhex(selector)
    dynpos=0
    for argtype in argtypes:
        if argtype in ("address", "uint256"):
            dynpos+=32
        elif argtype=="string":
            dynpos+=32
        else:
            raise TypeError('Serialization of "{0}" type is not implemented'.format(argtype))

    tail=b""
    for argtype, argvalue in zip(argtypes, args):
        if argtype=="address":
            if not isinstance(argvalue, str):
                raise TypeError('Argument of "address" type must be passed as a string')

            txdata+=12*b'\0'+bytes.fromhex(argvalue[2:])

        elif argtype=="uint256":
            if not isinstance(argvalue, str):
                raise TypeError('Argument of "uint256" type must be passed as a string')

            txdata+=int(argvalue, 0).to_bytes(32, "big")

        elif argtype=="string":
            txdata+=dynpos.to_bytes(32, "big")

            argvalue=argvalue.encode("utf8")

            tail+=len(argvalue).to_bytes(32, "big")
            dynpos+=32

            padded=argvalue+b'\0'*((32-len(argvalue)%32)%32)
            tail+=padded
            dynpos+=len(padded)

    return txdata+tail

class FunctionInvocation:
    def __init__(self, *, db, config, chainid, contract, sender, selector, argtypes, customResultHandler):
        self.db=db
        self.config=config
        self.chainid=chainid
        self.contract=contract
        self.sender=sender
        self.selector=selector
        self.argtypes=argtypes
        self.customResultHandler=customResultHandler

    def __call__(self, uuid, args):
        queue=ethqueue.Queue(db=self.db, config=self.config)
        queue.sendTransaction(
            uuid=uuid,
            **self.__makeTxArgs(args))

    def estimateFee(self, args):
        return ethfee.estimateFee(
            config=self.config,
            **self.__makeTxArgs(args))

    def __makeTxArgs(self, args):
        return dict(
            chainid=self.chainid,
            sender=self.sender,
            receiver=self.contract,
            value=0,
            data=makeTransactionData(self.selector, self.argtypes, args),
            customResultHandler=self.customResultHandler)

class Call:
    def __init__(self, *, config, chainid, contract, selector, argtypes, customResultHandler):
        self.config=config
        self.chainid=chainid
        self.contract=contract
        self.selector=selector
        self.argtypes=argtypes
        self.customResultHandler=customResultHandler

    def __call__(self, args):
        nodepool=NodePool(config=self.config)
        node=nodepool.connectToAnyNode(self.chainid)
        if node is None:
            raise cgijsonrpc.JsonRPCException(-1003, "ETH node is unavailable")

        data=makeTransactionData(self.selector, self.argtypes, args)
        res=node.eth_call(dict(to=self.contract, data="0x"+data.hex()), "latest")

        if self.customResultHandler is not None:
            customResultHandler=extapi.customResultHandler(self.customResultHandler)
            if customResultHandler:
                res=customResultHandler(res)

        return res

    def estimateFee(self, args):
        return 0

def register(*, db, config, registry):
    for coinDescription in ethconfig.listCoinDescriptions(config):
        for apiDescription in coinDescription.extAPI:
            try:
                if apiDescription["type"]=="sendTransaction":
                    registry.addMethod(
                        apiDescription["name"],
                        FunctionInvocation(
                            db=db,
                            config=config,
                            chainid=coinDescription.chainid,
                            contract=coinDescription.contract,
                            sender=apiDescription["sender"],
                            selector=apiDescription["selector"],
                            argtypes=apiDescription["args"],
                            customResultHandler=apiDescription.get("customResult")))

                elif apiDescription["type"]=="call":
                    registry.addMethod(
                        apiDescription["name"],
                        Call(
                            config=config,
                            chainid=coinDescription.chainid,
                            contract=coinDescription.contract,
                            selector=apiDescription["selector"],
                            argtypes=apiDescription["args"],
                            customResultHandler=apiDescription.get("customResult")))
            except (TypeError, KeyError):
                pass
