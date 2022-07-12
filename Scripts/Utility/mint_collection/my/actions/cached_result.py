#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

from .action import *


class cached_result(action):
    @classmethod
    def make_action_id(cls, action_id, result):
        return action_id

    def __init__(self, action_id, result):
        self.action_id = action_id
        self.result = result

    def idle(self):
        return None

    def is_finished(self):
        return True

    def get_result(self):
        return self.format_result(self.result)
