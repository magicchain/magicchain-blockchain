#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

import collections

CoinDescription=collections.namedtuple("CoinDescription", ["symbol", "chainid", "depositContract", "depositController", "hotWallet", "type", "contract", "parentCoinSymbol", "extAPI"])

def findCoinDescription(*, config, coin):
    for chainConfig in config["Ethereum"]:
        chainid=chainConfig["chainId"]
        depositContract=chainConfig.get("depositContract", None)
        depositController=chainConfig.get("depositController", None)
        hotWallet=chainConfig.get("hotWallet", None)

        if chainConfig["symbol"]==coin:
            return CoinDescription(
                symbol=coin,
                chainid=chainid,
                depositContract=depositContract,
                depositController=depositController,
                hotWallet=hotWallet,
                type="",
                contract=None,
                parentCoinSymbol=coin,
                extAPI=[])

        erc223_list=chainConfig.get("ERC223", None)
        if erc223_list is not None:
            for erc223 in erc223_list:
                if erc223["symbol"]==coin:
                    return CoinDescription(
                        symbol=coin,
                        chainid=chainid,
                        depositContract=depositContract,
                        depositController=depositController,
                        hotWallet=erc223.get("hotWallet", hotWallet),
                        type="ERC223",
                        contract=erc223["contract"],
                        parentCoinSymbol=chainConfig["symbol"],
                        extAPI=erc223.get("extAPI", []))

        erc721_list=chainConfig.get("ERC721", None)
        if erc721_list is not None:
            for erc721 in erc721_list:
                if erc721["symbol"]==coin:
                    return CoinDescription(
                        symbol=coin,
                        chainid=chainid,
                        depositContract=depositContract,
                        depositController=depositController,
                        hotWallet=erc721.get("hotWallet", hotWallet),
                        type="ERC721",
                        contract=erc721["contract"],
                        parentCoinSymbol=chainConfig["symbol"],
                        extAPI=erc721.get("extAPI", []))

    return None

def listCoinDescriptions(config):
    for chainConfig in config["Ethereum"]:
        chainid=chainConfig["chainId"]
        depositContract=chainConfig.get("depositContract", None)
        depositController=chainConfig.get("depositController", None)
        hotWallet=chainConfig.get("hotWallet", None)

        yield CoinDescription(
            symbol=chainConfig["symbol"],
            chainid=chainid,
            depositContract=depositContract,
            depositController=depositController,
            hotWallet=hotWallet,
            type="",
            contract=None,
            parentCoinSymbol=chainConfig["symbol"],
            extAPI=[])

        erc223_list=chainConfig.get("ERC223", None)
        if erc223_list is not None:
            for erc223 in erc223_list:
                yield CoinDescription(
                    symbol=erc223["symbol"],
                    chainid=chainid,
                    depositContract=depositContract,
                    depositController=depositController,
                    hotWallet=erc223.get("hotWallet", hotWallet),
                    type="ERC223",
                    contract=erc223["contract"],
                    parentCoinSymbol=chainConfig["symbol"],
                    extAPI=erc223.get("extAPI", []))

        erc721_list=chainConfig.get("ERC721", None)
        if erc721_list is not None:
            for erc721 in erc721_list:
                yield CoinDescription(
                    symbol=erc721["symbol"],
                    chainid=chainid,
                    depositContract=depositContract,
                    depositController=depositController,
                    hotWallet=erc721.get("hotWallet", hotWallet),
                    type="ERC721",
                    contract=erc721["contract"],
                    parentCoinSymbol=chainConfig["symbol"],
                    extAPI=erc721.get("extAPI", []))

def getPrimaryCoinSymbol(*, config, chainid):
    for desc in listCoinDescriptions(config):
        if desc.type=="" and desc.chainid==chainid:
            return desc.symbol
    return None
