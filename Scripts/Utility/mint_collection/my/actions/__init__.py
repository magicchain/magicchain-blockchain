#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

import sys
import importlib
import my
# to simplify importing and subclassing
from .action import *
from .cached_result import *
from .group_executor import *


def create(name, *args, cache = True, run = True, **kwargs):
    mod = importlib.import_module("."+name, __name__)
    cls = getattr(mod, name)

    if not cache:
        act = cls(*args, **kwargs)

    else:
        action_id = cls.make_action_id(*args, **kwargs)
        human_readable_name = cls.make_human_readable_name(*args, **kwargs)

        try:
            res = my.statedb.cache.find_result(action_id)

            act = cached_result(action_id, res)

            act.format_result = lambda result: cls.format_result(result, *args, **kwargs)
            if human_readable_name is not None:
                act.human_readable_name = human_readable_name+" (CACHED)"
                print("{0}: {1}".format(action_id, act.human_readable_name))

            return act

        except KeyError:
            pass

        act = cls(*args, **kwargs)

        def set_result_handler(result):
            my.statedb.cache.store_result(action_id, result)
            act.__class__.set_result(act, result)

        act.set_result = set_result_handler

    act.format_result = lambda result: cls.format_result(result, *args, **kwargs)

    if act.human_readable_name is not None:
        print("{0}: {1}".format(action_id, act.human_readable_name))

    if run:
        act.run()

    return act
