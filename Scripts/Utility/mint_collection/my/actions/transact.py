#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

import time
import json
import web3.datastructures
import hexbytes
import my
import my.crypto.secp256k1
import my.crypto.ethereum


class transact(my.actions.action):
    @classmethod
    def make_action_id(cls, *, sender_prv, receiver, value = 0, gas_price = None, gas_limit = None, payload = '', **kwargs):
        # Do not use gas_price and gas_limit in hash calculation
        return super().make_action_id(sender_prv=sender_prv, receiver=receiver, value=value, payload=payload, **kwargs)

    @staticmethod
    def format_result(result, *args, **kwargs):
        return json.loads(result)

    @staticmethod
    def encode_receipt(receipt):
        class CustomEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, web3.datastructures.AttributeDict):
                    return obj.__dict__

                if isinstance(obj, hexbytes.HexBytes):
                    return obj.hex()

                return json.JSONEncoder.default(self, obj)

        return json.dumps(receipt, ensure_ascii=True, indent=None, sort_keys=True, separators=(',', ':'), cls=CustomEncoder)

    def __init__(self, *, sender_prv, receiver, value = 0, gas_price = None, gas_limit = None, payload = '', **kwargs):
        super().__init__()

        if len(sender_prv)!=66 or not sender_prv.startswith("0x"):
            raise ValueError("Invalid format of sender private key")

        self.sender_prv = sender_prv

        sender_pub = my.crypto.secp256k1.makePublicKey(bytes.fromhex(sender_prv[2:]))
        sender = my.crypto.ethereum.makeAddress(sender_pub)

        self.request_id = self.action_id

        if isinstance(payload, str) and payload.startswith("0x"):
            payload = payload[2:]

        my.statedb.ethqueue.add_new_request(self.request_id,
                                            sender    = my.geth.toChecksumAddress(sender),
                                            receiver  = my.geth.toChecksumAddress(receiver) if receiver is not None else None,
                                            value     = value,
                                            gas_price = gas_price,
                                            gas_limit = gas_limit,
                                            payload   = payload)

    def idle(self):
        if self.is_finished():
            return

        request = my.statedb.ethqueue.get_request(self.request_id)
        if request is None:
            return

        if request.status<0:
            # must be string.
            self.set_result(request.status)
            return

        elif request.status==0:
            self.set_result(request.receipt)
            return

        if request.status==1:
            request = self.__start_handling(request)

        if request.status==2:
            request = self.__assign_gas_limit(request)

        if request.status==3:
            request = self.__assign_gas_price(request)

        if request.status==4:
            request = self.__assign_nonce(request)

        if request.status==5:
            self.__broadcast_transaction(request)
            return

        if request.status==6:
            self.__check_completion(request)

    def __start_handling(self, request):
        request = request._replace(status = 2)

        print("{0}: new pending request".format(self.request_id))
        my.statedb.ethqueue.update_request(self.request_id, status = request.status)

        return request

    def __assign_gas_limit(self, request):
        gas_limit = request.gas_limit
        if gas_limit is None:
            try:
                max_gas = my.geth.eth.getBlock("latest").gasLimit
            except:
                max_gas = 8000000

            gas_limit = max_gas
            request = request._replace(gas_limit = gas_limit)

            gas_limit = self.__estimate_gas(request)

            request = request._replace(gas_limit = gas_limit)

            gas_limit = self.__estimate_gas(request)

            request = request._replace(gas_limit = gas_limit, status = 3)

            print("{0}: assigned gas limit {1}".format(self.request_id, request.gas_limit))
            my.statedb.ethqueue.update_request(self.request_id,
                                               status    = request.status,
                                               gas_limit = request.gas_limit)
        else:
            request = request._replace(status = 3)
            my.statedb.ethqueue.update_request(self.request_id, status = request.status)

        return request

    def __assign_gas_price(self, request):
        if request.gas_price is None:
            request = request._replace(gas_price = my.geth.eth.gas_price)

            print("{0}: assigned gas price {1}".format(self.request_id, request.gas_price))

        request = request._replace(status = 4, fee_increment_timestamp = round(1000*time.time()))

        my.statedb.ethqueue.update_request(self.request_id,
                                           status                  = request.status,
                                           gas_price               = request.gas_price,
                                           fee_increment_timestamp = request.fee_increment_timestamp)

        return request

    def __assign_nonce(self, request):
        net_nonce = my.geth.eth.get_transaction_count(request.sender, "pending")

        db_nonce = my.statedb.ethqueue.find_highest_nonce(request.sender)
        if db_nonce is None:
            nonce=net_nonce
        else:
            nonce = max(db_nonce+1, net_nonce)

        request = request._replace(nonce = nonce, status = 5)

        print("{0}: assigned nonce {1}".format(self.request_id, request.nonce))
        my.statedb.ethqueue.update_request(self.request_id,
                                           status = request.status,
                                           nonce  = request.nonce)

        return request

    def __broadcast_transaction(self, request):
        prev_txhashes = []
        if request.txhash is not None:
            prev_txhashes = request.txhash.split(":")

        tx = self.__make_tx_object(request)
        signed = my.geth.eth.account.sign_transaction(tx, self.sender_prv)

        try:
            txhash = my.geth.eth.send_raw_transaction(signed.rawTransaction)
            txhash = txhash.hex()
        except ValueError as e:
            if e.args[0]=={"code": -32000, "message": "nonce too low"} or e.args[0]=={"code": -32000, "message": "already known"}:
                txhash = signed.hash.hex()
            else:
                raise

        if len(prev_txhashes)==0 or prev_txhashes[-1]!=txhash:
            prev_txhashes.append(txhash)

        request = request._replace(status               = 6,
                                   txhash               = ":".join(prev_txhashes),
                                   send_timestamp       = round(1000*time.time()),
                                   next_check_timestamp = round(1000*(time.time()+15)))

        print("{0}: broadcasted transaction {1}".format(self.request_id, txhash))

        my.statedb.ethqueue.update_request(self.request_id,
                                           status               = request.status,
                                           txhash               = request.txhash,
                                           send_timestamp       = request.send_timestamp,
                                           next_check_timestamp = request.next_check_timestamp)

        return request

    def __check_completion(self, request):
        txhashes = request.txhash.split(":")

        receipt = None
        for txhash in txhashes[::-1]:
            try:
                receipt = my.geth.eth.get_transaction_receipt(txhash)
            except web3.exceptions.TransactionNotFound:
                receipt = None

            if receipt is not None:
                break

        if receipt is None:
            if 1000*time.time()>=request.send_timestamp+1028*1000:
                # Rebroadcast transaction every 17+ minutes without changes
                request = request._replace(status = 5)
                my.statedb.ethqueue.update_request(self.request_id,
                                                   status = request.status)

                return self.__broadcast_transaction(request)

            if 1000*time.time()>=request.fee_increment_timestamp+3600*1000:
                request = request._replace(fee_increment_timestamp = round(1000*time.time()),
                                           gas_price               = round(request.gas_price*1.125),
                                           status                  = 5)

                my.statedb.ethqueue.update_request(self.request_id,
                                                   status                  = request.status,
                                                   gas_price               = request.gas_price,
                                                   fee_increment_timestamp = request.fee_increment_timestamp)

                print("{0}: bumping gas price up to {1}".format(self.request_id, request.gas_price))

                return self.__broadcast_transaction(request)

            my.statedb.ethqueue.retry_after(self.request_id, seconds = 5)

            return request

        receipt = self.encode_receipt(receipt)
        request = request._replace(status = 0,
                                   receipt = receipt)

        my.statedb.ethqueue.update_request(self.request_id,
                                           status  = request.status,
                                           receipt = request.receipt)

        print("{0}: receipt received".format(self.request_id))

        return request

    @staticmethod
    def __make_tx_object(request):
        tx = {}

        tx["from"]    = request.sender
        tx["gas"]     = request.gas_limit
        tx["value"]   = request.value
        tx["data"]    = bytes.fromhex(request.payload)
        #tx["type"]    = None # legacy
        tx["chainId"] = my.geth.eth.chain_id

        if request.receiver is not None:
            tx["to"] = request.receiver

        if request.gas_price is not None:
            tx["gasPrice"] = request.gas_price

        if request.nonce is not None:
            tx["nonce"] = request.nonce

        return tx

    def __estimate_gas(self, request):
        tx = self.__make_tx_object(request)

        # Low gas price may prevent gas limit calculation
        # ("err: max fee per gas less than block base fee")
        del tx["gasPrice"]

        return 100000+round(my.geth.eth.estimate_gas(tx)*1.05)
