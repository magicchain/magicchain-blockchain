import json
import web3
from solc import compile_source, compile_standard, compile_files
from web3.middleware import geth_poa_middleware
import sys
import os

import hashlib

if(len(sys.argv)>=7):
    # contact source path
    srcContrPath=sys.argv[1]
    # deployed contract name as it appears in source code
    deployedContactName=sys.argv[2]
    # compiled contract output path
    compileOut=sys.argv[3]
    # address of deployer user
    deployerAddress=sys.argv[4]
    # deployed contract address file path
    addrPath=sys.argv[5]
    # geth ipc connection path
    ipcGethPath=sys.argv[6]
    # contact params
    ctorParams=[]
    for i in range(7, len(sys.argv)):
        ctorParams.append("{0}".format(sys.argv[i]))
else:
    print("invalid argument for py-script")
    exit(1)

print(*ctorParams)

compiledFileName=compileOut+'/combined.json'
contractName=os.path.splitext(os.path.basename(srcContrPath))[0]

print(os.path.splitext(os.path.basename(srcContrPath))[0])

ipcCon=web3.Web3(web3.Web3.IPCProvider(ipcGethPath))
# FOR TEST NET ONLY: inject the poa compatibility middleware to the innermost layer.
#ipcCon.middleware_stack.inject(geth_poa_middleware, layer=0)
print(ipcCon.eth.blockNumber)

os.system("solc --combined-json abi,asm,ast,bin,bin-runtime,interface,opcodes --optimize --overwrite -o {0} {1}".format(compileOut, srcContrPath))

with open(compiledFileName, 'r') as myfile:
    compiledSol=json.load(myfile)

contractInterface=compiledSol["contracts"][srcContrPath+":"+deployedContactName]

if(deployerAddress=="0"):
    deployerAddress = ipcCon.eth.coinbase
elif deployerAddress!=ipcCon.eth.coinbase:
    deployerAddress=ipcCon.toChecksumAddress(deployerAddress)
print(deployerAddress)
print(srcContrPath+":"+contractName)
# Instantiate and deploy contract
print("Contact bin size={0}".format(len(contractInterface['bin'])/2))

md5Contract=hashlib.md5(contractInterface['bin'].encode('utf-8')).hexdigest()
print("Contact md5 cksum size={0}".format(md5Contract))

# debug only. should be commented out.
#with open('bin_imp.txt', 'w') as myfile:
#    myfile.write(contractInterface['bin'])
#with open('asm_imp.txt', 'w') as myfile:
#    json.dump(contractInterface['asm'], myfile)

contractType=ipcCon.eth.contract(abi=contractInterface['abi'], bytecode=contractInterface['bin'])
tx = {'gas': 6000000, 'from': deployerAddress}

#tx1 = {'gas': 6000000, 'from': deployAddress, 'data': contractInterface['bin']}
if len(ctorParams)==0:
    tx_hash = contractType.constructor().transact(tx)
else:
    tx_hash=contractType.constructor(*ctorParams).transact(tx)
tx_receipt=ipcCon.eth.waitForTransactionReceipt(tx_hash)
print("deploy status=", tx_receipt.status, tx_receipt)
if(tx_receipt.status==0):
    print("can't deploy, aborting...")
    exit(1)
print("deploy gasUsed=", tx_receipt, "contract address={}".format(tx_receipt.contractAddress))

with open(addrPath, 'w') as myfile:
    myfile.write(tx_receipt.contractAddress)
