#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

import requests, json, uuid, hmac, hashlib, binascii


class Notifier:
    def __init__(self, *, config):
        self.url=config["notify-url"]
        self.hmacKeyId=config.get("security", {}).get("hmac-keyid", None)
        key=config.get("security", {}).get("hmac-key", None)
        self.hmacKey=key and binascii.a2b_hex(key)

    def sendNotification(self, methodName, **kwargs):
        data=Notifier.__serializeMethodCall(methodName=methodName, id=None, params=kwargs)
        headers=self.__makeHeaders(data)

        try:
            requests.post(self.url, data=data, headers=headers)
        except:
            pass

    def sendData(self, methodName, **kwargs):
        id=str(uuid.uuid4())
        data=Notifier.__serializeMethodCall(methodName=methodName, id=id, params=kwargs)
        headers=self.__makeHeaders(data)

        try:
            r=requests.post(self.url, data=data, headers=headers)
            r.raise_for_status()

            if self.hmacKey is not None:
                digest=hmac.new(self.hmacKey, r.content, hashlib.sha256).hexdigest()
                sig=r.headers.get("HMAC-Signature")

                if digest!=sig:
                    return None

            j=r.json()
            if j["jsonrpc"]=="2.0" and "result" in j and j.get("error") is None and j["id"]==id:
                return j["result"]

        except:
            pass

        return None

    @staticmethod
    def __serializeMethodCall(*, methodName, id=None, params):
        r={}
        r["jsonrpc"]="2.0"
        r["method"]=methodName
        r["params"]=params
        if id is not None:
            r["id"]=id

        return json.dumps(r).encode("utf8")

    def __makeHeaders(self, data):
        headers={}
        headers["Content-Type"]="application/json"
        if self.hmacKeyId is not None:
            headers["HMAC-KeyId"]=self.hmacKeyId
        if self.hmacKey is not None:
            digest=hmac.new(self.hmacKey, data, hashlib.sha256).hexdigest()
            headers["HMAC-Signature"]=digest

        return headers
