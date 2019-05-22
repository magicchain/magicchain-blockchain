#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

import os, sys, json, time, hashlib, hmac

class Handler:
    def __init__(self):
        self.methods={}
        self.outgoingHMACKeyId=None
        self.outgoingHMACKey=None

    def addMethod(self, name, function):
        self.methods[name]=function

    # TODO: setIncomingHMAC, allow multiple key ids with distinct hmac keys

    def setOutgoingHMAC(self, keyid, key):
        self.outgoingHMACKeyId=keyid
        self.outgoingHMACKey=key

    def run(self):
        if os.environ.get("REQUEST_METHOD")!="POST":
            sys.stdout.write("Status: 405 Method Not Allowed\n\nOnly POST method is allowed\n")
            return

        if os.environ.get("CONTENT_TYPE")!="application/json":
            sys.stdout.write("Status: 415 Unsupported Media Type\n\nOnly application/json content type is supported\n")
            return

        data=sys.stdin.read()

        # TODO: check request HMAC if needed


        try:
            j=json.loads(data)
        except json.decoder.JSONDecodeError:
            self.printReply(Handler.makeErrorReply(-32700, "Parse error", None))
            return

        if isinstance(j, list):
            if not j: # empty list
                self.printReply(Handler.makeErrorReply(-32600, "Invalid Request", None))
            else:
                res=[]
                for requestObject in j:
                    replyObject=self.handleRequestObject(requestObject)
                    if replyObject is not None:
                        res.append(replyObject)
                if not res:
                    self.printReplyString("")
                else:
                    self.printReply(res)
        else:
            replyObject=self.handleRequestObject(j)
            if replyObject is None:
                self.printReplyString("")
            else:
                self.printReply(replyObject)

    def handleRequestObject(self, requestObject):
        # id

        if "id" in requestObject and not isinstance(requestObject["id"], (str, int, float, type(None))):
            return Handler.makeErrorReply(-32600, "Invalid Request", None)

        isNotification=("id" not in requestObject)
        id=requestObject.get("id")

        # Check if the request object is valid

        isValid=True
        if requestObject.get("jsonrpc")!="2.0":
            isValid=False

        if "method" not in requestObject or not isinstance(requestObject["method"], str):
            isValid=False

        if "params" in requestObject and not isinstance(requestObject, (list, dict)):
            isValid=False

        if not isValid:
            return None if isNotification else Handler.makeErrorReply(-32600, "Invalid Request", id)

        # Find corresponding method handler, invoke it

        method=requestObject["method"]
        if method not in self.methods:
            return None if isNotification else Handler.makeErrorReply(-32601, "Method not found", id)

        try:
            if "params" not in requestObject:
                res=self.methods[method]()
            elif isinstance(requestObject["params"], list):
                res=self.methods[method](*requestObject["params"])
            else:
                res=self.methods[method](**requestObject["params"])
        except TypeError:
            return None if isNotification else Handler.makeErrorReply(-32602, "Invalid params", id)
        # TODO: handle user-defined exception

        return None if isNotification else Handler.makeResultReply(res, id)

    @staticmethod
    def makeResultReply(result, id):
        return {"jsonrpc": "2.0", "id": id, "result": result}

    @staticmethod
    def makeErrorReply(code, message, id):
        return {"jsonrpc": "2.0", "id": id, "error": {"code": code, "message": message}}

    def printReply(self, j):
        self.printReplyString(json.dumps(j, indent=None))

    def printReplyString(self, s):
        s=s.encode("utf8")
        buf=sys.stdout.buffer

        buf.write(b"Status: 200 OK\n")
        buf.write(b"Content-Type: application/json\n")

        if self.outgoingHMACKeyId is not None:
            buf.write(b"HMAC-KeyId: "+self.outgoingHMACKeyId.encode("utf8")+b"\n")
        if self.outgoingHMACKey is not None:
            nonce="{0}".format(int(time.time()*1000)).encode("latin1")
            digest=hmac.new(self.outgoingHMACKey, s+nonce, hashlib.sha256).hexdigest().encode("latin1")

            buf.write(b"HMAC-Nonce: "+nonce+b"\n")
            buf.write(b"HMAC-Signature: "+digest+b"\n")

        buf.write(b"\n"+s)
