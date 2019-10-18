#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj


class Registry:
    def __init__(self):
        self.methods={}

    def addMethod(self, name, function):
        self.methods[name]=function

    def __contains__(self, name):
        return name in self.methods

    def __getitem__(self, name):
        return self.methods[name]
