#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

import time
import json
import hashlib


class action:
    @classmethod
    def make_action_id(cls, *args, **kwargs):
        s = json.dumps([cls.__name__, args, kwargs], ensure_ascii=True, indent=None, sort_keys=True, separators=(',', ':'))
        h = hashlib.md5(s.encode("latin1")).hexdigest()
        return h

    @classmethod
    def make_human_readable_name(cls, *args, **kwargs):
        return None

    @staticmethod
    def format_result(result, *args, **kwargs):
        return result

    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls)
        obj.action_id = cls.make_action_id(*args, **kwargs)
        obj.human_readable_name = cls.make_human_readable_name(*args, **kwargs)
        obj.format_result = lambda result: cls.format_result(result, args, kwargs)
        return obj

    def __init__(self):
        self.result = None
        self.finished = False

    def wait(self, max_time = None):
        if self.is_finished():
            return self.get_result()

        deadline = None if max_time is None else (time.time()+max_time)
        while True:
            if deadline is not None and time.time()>=deadline:
                return None

            self.idle()
            if self.is_finished():
                return self.get_result()

            time.sleep(1)

    def run(self):
        self.idle()

    def idle(self):
        # It's expected that derived class will eventually call set_result from
        # within its overloaded implementation of idle()

        raise NotImplementedError()

    def is_finished(self):
        return self.finished

    def get_result(self):
        return self.format_result(self.result)

    def get_raw_result(self):
        return self.result

    def set_result(self, result):
        self.result = result
        self.finished = True

    def __add__(self, other):
        return multi_action([self, other])


class multi_action(action):
    @classmethod
    def make_action_id(cls, *args, **kwargs):
        return None

    def __init__(self, children):
        super().__init__()
        self.children=children

    def idle(self):
        for child in self.children:
            if not child.is_finished():
                child.idle()

    def is_finished(self):
        return all((child.is_finished() for child in self.children))

    def get_result(self):
        return [child.get_result() for child in self.children]

    def __add__(self, other):
        return multi_action(self.children.copy()+[other])

    def __radd__(self, other):
        return multi_action([other]+self.children.copy())
