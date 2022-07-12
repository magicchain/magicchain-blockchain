#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

import functools
import time


class group_executor:
    def __init__(self, group_size = 100, result_handler = None):
        self.group_size = group_size
        self.result_handler = result_handler
        self.actions = []

    def add_action(self, action):
        if action.is_finished():
            if self.result_handler is not None:
                self.result_handler(action, action.get_result())
        else:
            for a in self.actions:
                a.idle()

            self.actions = self.__get_still_running_actions()

            self.actions.append(action)

            if len(self.actions)>=self.group_size:
                self.__execute(self.group_size//2)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.__execute(0)

    def __get_still_running_actions(self):
        running_actions = []
        for action in self.actions:
            if action.is_finished():
                if self.result_handler is not None:
                    self.result_handler(action, action.get_result())
            else:
                running_actions.append(action)

        return running_actions

    def __execute(self, leave_running):
        self.actions = self.__get_still_running_actions()

        while len(self.actions)>leave_running:
            for action in self.actions:
                action.idle()

            still_running = self.__get_still_running_actions()
            if len(still_running)==len(self.actions):
                time.sleep(0.5)
            else:
                self.actions = still_running
