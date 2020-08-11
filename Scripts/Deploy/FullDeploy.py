import json
import sys
import os
import shutil

# import our modules
commonImportDir=os.path.realpath(os.path.join(os.path.dirname(sys.argv[0]), '../Common'))
sys.path.append(commonImportDir)

import EstIpcConnection


if(len(sys.argv)>=2):
    # path of ipc connection to geth
    ipcGethPath=sys.argv[1]
else:
    print("invalid argument for py-script. Use: FullDeploy.py <contacts source dir> <deployer address> <path of ipc connection to geth>", sys.argv, len(sys.argv))
    exit(1)

if len(sys.argv)>=3:
    # contacts source dir
    srcContrPath=os.path.abspath(sys.argv[2])
    
else:
    srcContrPathOrig=os.path.realpath(os.path.join(os.path.dirname(sys.argv[0]), 'smartcontracts'))
    srcContrPath=os.path.realpath(os.path.join(srcContrPathOrig, '../build'))

if len(sys.argv)>=4:
    # deployer address
    deployerAddress=sys.argv[3]
else:
    deployerAddress='0'

if deployerAddress == "0":
    ipcCon = EstIpcConnection.estOnlyConnection(ipcGethPath, True)
    print("full dep deployer", deployerAddress)
    deployerAddress = ipcCon.eth.coinbase

buildDir=srcContrPath
contractAddress=''
contractName='MagicChain721'
contractFileName='MagicChain721.sol'
compileOut=os.path.join(buildDir, 'out'+contractName)
addrPath=os.path.join(buildDir, contractName+'Address.txt')

packageData={
"scripts": {
"build-contracts": "sol-merger \"{0}/*.sol\" ./build".format(srcContrPathOrig)
},
"devDependencies": {
"sol-merger": "^3.1.0"
}
}

with open('package.json', 'w') as myfile:
    json.dump(packageData, myfile)


#if not os.path.exists('node_modules/github.com/OpenZeppelin'):
#    os.makedirs('node_modules/github.com/OpenZeppelin')

if not os.path.exists('smartcontracts'):
    shutil.copytree('../../smartcontracts', 'smartcontracts')
if not os.path.exists('node_modules/github.com/OpenZeppelin/openzeppelin-contracts'):
    shutil.copytree('../../../openzeppelin-contracts-master', 'node_modules/github.com/OpenZeppelin/openzeppelin-contracts')

os.system("npm run build-contracts")

os.system("python3 DeployContract.py {0} {1} {2} {3} {4} {5}"
          .format(srcContrPath+"/"+contractFileName, contractName, compileOut, deployerAddress, addrPath, ipcGethPath))

try:
    with open(addrPath, 'r') as myfile:
        contractAddress = myfile.read()
except Exception:
    print("Contract is not deployed")
    exit(1)

print("Full deploy success. Contract address={0}".format(contractAddress))
