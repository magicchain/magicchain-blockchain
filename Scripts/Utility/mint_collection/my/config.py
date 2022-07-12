#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

import sys
import os
import re


def expand_variables(string, variables):
    # It doesn't expand recursive shit like ${FOO_${BAR}}. Why? Because fuck you!

    regexp=re.compile("\\$\\{[^}]+\\}")

    while True:
        match=re.search(regexp, string)
        if not match:
            break

        varname=match.group(0)[2:-1]
        replacement=variables.get(varname, "")

        string=string[:match.span()[0]]+replacement+string[match.span()[1]:]

    return string

def load(filename):
    class Config:
        pass

    current_section=None
    config=Config()

    variables=os.environ.copy()
    variables.update(BINDIR=os.path.dirname(os.path.realpath(sys.argv[0])))

    with open(filename, "rt") as f:
        for (lineno, l) in enumerate(f.readlines(), 1):
            l=l.partition('#')[0].strip()
            if len(l)==0:
                continue
            elif l.startswith('[') and l.endswith(']'):
                current_section=l[1:-1]
            else:
                (name,sep,value)=l.partition('=')
                if sep!='=':
                    raise ValueError("Invalid config file line {0}".format(lineno))

                name=name.strip()
                value=value.strip()

                try:
                    name=expand_variables(name, variables)
                    value=expand_variables(value, variables)
                except:
                    raise ValueError("Failed to expand variable in config file line {0}".format(lineno))

                if current_section is None:
                    setattr(config, name, value)
                else:
                    if not hasattr(config, current_section):
                        setattr(config, current_section, Config())
                    setattr(getattr(config, current_section), name, value)

    return config
