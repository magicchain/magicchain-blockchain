#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

import sys
import csv
import os
import requests
import magic
import uuid as uuidlib
import io
from PIL import Image
import my

(caller_prv, caller_address) = my.privkey.get_private_key_and_address(my.config.contracts.caller)

MintMe = my.Contract("MintMe", my.config.contracts.MintMe)

def scale_down_image(data, scale_factor):
    img = Image.open(io.BytesIO(data))
    w, h = img.size
    new_w, new_h = round(w/scale_factor), round(h/scale_factor)

    img = img.resize((new_w, new_h), Image.ANTIALIAS)

    buf = io.BytesIO()
    img.save(buf, "PNG")

    return buf.getvalue()

def add_action(content, ge):
    a = my.actions.create("call_method_mint",
                          contract   = MintMe,
                          caller_prv = caller_prv,
                          address    = my.config.contracts.mint_target,
                          content    = content,
                          fee        = int(my.config.contracts.fee))
    a.content = content

    ge.add_action(a)

def mint(image, title, description, ge):
    img_data = open(os.path.join(my.config.source.image_dir, image), "rb").read()
    img_mime_type = magic.from_buffer(img_data, mime=True)

    r = requests.post(my.config.storage.url,
                      data=img_data,
                      headers={"Content-Type": img_mime_type})
    r.raise_for_status()
    img_cid = r.text.strip()

    if hasattr(my.config.source, "cover_scale_factor") and abs(float(my.config.source.cover_scale_factor)-1.0)>1.0E-7:
        cover_data = scale_down_image(img_data, float(my.config.source.cover_scale_factor))
        cover_mime_type = magic.from_buffer(cover_data, mime=True)

        r = requests.post(my.config.storage.url,
                          data=cover_data,
                          headers={"Content-Type": cover_mime_type})
        r.raise_for_status()
        cover_cid = r.text.strip()
    else:
        cover_cid = img_cid

    uuid = uuidlib.uuid5(uuidlib.UUID("2d9ee027-6b51-4423-b12e-cab42871e6e1"), f"{img_cid}:{title}:{description}")

    r = requests.post(my.config.storage.url,
                      json={"name":         title,
                            "description":  description,
                            "image":        f"ipfs://{cover_cid}",
                            "content":      f"ipfs://{img_cid}",
                            "external_url": f"https://mintme.global/token/{my.config.contracts.blockchain}/{my.config.contracts.MintMe}/{uuid}"})
    r.raise_for_status()
    content = r.text.strip()

    add_action(content, ge)

class ReceiptHandler:
    def __init__(self):
        self.failed = []

    def __call__(self, action, receipt):
        if receipt["status"]==0:
            self.failed.append(action.content)

rh = ReceiptHandler()
with open(my.config.source.csv_file, newline = "") as f:
    reader = csv.reader(f, delimiter = ";")
    reader.__next__() # skip header line

    with my.actions.group_executor(100, rh) as ge:
        for image, title, description in reader:
            mint(image, title, description, ge)

while len(rh.failed)>0:
    failed = rh.failed

    rh = ReceiptHandler()
    with my.actions.group_executor(100, rh):
        for content in failed:
            add_action(content, ge)
