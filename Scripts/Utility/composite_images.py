#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

import sys
import argparse
import os
from PIL import Image


parser = argparse.ArgumentParser(description="Image compose utility", prog=sys.argv[0])
parser.add_argument("--backgrounds", help="Specify directory name where background images are stored")
parser.add_argument("--foregrounds", help="Specify directory name where foreground images are stored")
parser.add_argument("--result", help="Specify directory name where result should be stored")

args = parser.parse_args(sys.argv[1:])

if not all((args.foregrounds, args.backgrounds, args.result)):
    parser.print_usage()
    sys.exit(1)

backgrounds_dir = args.backgrounds
foregrounds_dir = args.foregrounds
result_dir = args.result

os.makedirs(result_dir, exist_ok=True)

for background_fn in os.listdir(backgrounds_dir):
    background = Image.open(os.path.join(backgrounds_dir, background_fn))
    for foreground_fn in os.listdir(foregrounds_dir):
        foreground = Image.open(os.path.join(foregrounds_dir, foreground_fn))

        res = Image.alpha_composite(background, foreground)

        res_fn = os.path.join(result_dir, os.path.splitext(foreground_fn)[0]+'-'+os.path.splitext(background_fn)[0]+".png")
        res.save(res_fn, "PNG")
