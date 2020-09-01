import json
import web3
from web3.middleware import geth_poa_middleware
import os

def estOnlyConnection(gethIpcPath, isDevNet):
    ipcCon=web3.Web3(web3.Web3.IPCProvider(gethIpcPath))
    # FOR TEST NET ONLY: inject the poa compatibility middleware to the innermost layer.
    if isDevNet:
        # It was like that before the version web3 v4. was renamed in web5.
        # ipcCon.middleware_stack.inject(geth_poa_middleware, layer=0)
        ipcCon.middleware_onion.inject(geth_poa_middleware, layer=0)
        ipcCon.eth.defaultAccount=ipcCon.eth.coinbase
    print(ipcCon.eth.blockNumber)

    return ipcCon


def estConnection(gethIpcPath, isDevNet, contractAddr, compiledSolPath, contractPath, deployedContactName):
    contractName=os.path.splitext(os.path.basename(contractPath))[0]
    print('estConnection params=', contractAddr, compiledSolPath, contractPath, contractName)

    ipcCon=web3.Web3(web3.Web3.IPCProvider(gethIpcPath))
    # FOR TEST NET ONLY: inject the poa compatibility middleware to the innermost layer.
    if isDevNet:
        # It was like that before the version web3 v4. was renamed in web5.
        # ipcCon.middleware_stack.inject(geth_poa_middleware, layer=0)
        ipcCon.middleware_onion.inject(geth_poa_middleware, layer=0)
        ipcCon.eth.defaultAccount=ipcCon.eth.coinbase
    print(ipcCon.eth.blockNumber)

    with open(compiledSolPath, 'r') as myfile:
        compiledSol=json.load(myfile)
    contractInterface=compiledSol["contracts"]['{}:{}'.format(contractPath, deployedContactName)]
    
    # Create the contract instance with the newly-deployed address
    contractIns=ipcCon.eth.contract(
        address=contractAddr,
        abi=contractInterface['abi'])

    return (ipcCon, contractIns)
