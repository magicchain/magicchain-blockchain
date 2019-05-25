#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

import collections

CoinDescription=collections.namedtuple("CoinDescription", ["symbol", "chainid", "depositContract", "depositController", "type", "contract", "parentCoinSymbol"])

def findCoinDescription(*, config, coin):
    for chainConfig in config["Ethereum"]:
        chainId=chainConfig["chainId"]
        depositContract=chainConfig.get("depositContract", None)
        depositController=chainConfig.get("depositController", None)

        if chainConfig["symbol"]==coin:
            return CoinDescription(coin, chainId, depositContract, depositController, "", None, coin)

        erc223_list=chainConfig.get("ERC223", None)
        if erc223_list is not None:
            for erc223 in erc223_list:
                if erc223["symbol"]==coin:
                    return CoinDescription(coin, chainId, depositContract, depositController, "ERC223", erc223["contract"], chainConfig["symbol"])

        erc721_list=chainConfig.get("ERC721", None)
        if erc721_list is not None:
            for erc721 in erc721_list:
                if erc721["symbol"]==coin:
                    return CoinDescription(coin, chainId, depositContract, depositController, "ERC721", erc721["contract"], chainConfig["symbol"])

    return None

def listCoinDescriptions(config):
    for chainConfig in config["Ethereum"]:
        chainId=chainConfig["chainId"]
        depositContract=chainConfig.get("depositContract", None)
        depositController=chainConfig.get("depositController", None)

        yield CoinDescription(chainConfig["symbol"], chainId, depositContract, depositController, "", None, chainConfig["symbol"])

        erc223_list=chainConfig.get("ERC223", None)
        if erc223_list is not None:
            for erc223 in erc223_list:
                yield CoinDescription(erc223["symbol"], chainId, depositContract, depositController, "ERC223", erc223["contract"], chainConfig["symbol"])

        erc721_list=chainConfig.get("ERC721", None)
        if erc721_list is not None:
            for erc721 in erc721_list:
                yield CoinDescription(erc721["symbol"], chainId, depositContract, depositController, "ERC721", erc721["contract"], chainConfig["symbol"])
