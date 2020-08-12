import json
import sys
import os
import shutil
import subprocess

# import our modules
commonImportDir=os.path.realpath(os.path.join(os.path.dirname(sys.argv[0]), '../Common'))
sys.path.append(commonImportDir)

import EstIpcConnection


helpStr="Use: FullDeploy.py <path of ipc connection to geth> " \
        "<open zeppelin contracts path>='../../../openzeppelin-contracts-master' " \
        "<contract deployer address>=0 <install sol-merger locally>=0 (available vals: 0|1)." \
        "Use 0 or omit it to set the default parameter."

if(len(sys.argv)>=2):
    if(sys.argv[1]=='--help'):
        print(helpStr)
        exit(0)
    # path of ipc connection to geth
    ipcGethPath=sys.argv[1]
else:
    print("invalid argument for py-script. "+helpStr)
    exit(1)

# Open Zeppelin contracts dir
openZeppContracts=os.path.join(os.path.dirname(sys.argv[0]), '../../../openzeppelin-contracts-master')
if len(sys.argv)>=3:
    if(sys.argv[2]!='0'):
        openZeppContracts=os.path.abspath(sys.argv[2])

deployerAddress='0'
if len(sys.argv)>=4:
    if(sys.argv[3]!='0'):
        deployerAddress=sys.argv[3]

if deployerAddress == "0":
    ipcCon = EstIpcConnection.estOnlyConnection(ipcGethPath, True)
    print("full dep deployer", deployerAddress)
    deployerAddress = ipcCon.eth.coinbase
    
if len(sys.argv)>=5:
    if(sys.argv[4]=='1'):
        isSolMergerInstalled=False
        try:
            output = subprocess.check_output("npm list sol-merger", shell=True)
            isSolMergerInstalled=('empty' not in output.decode("utf-8"))
        except Exception:
            print("'npm list sol-merger' catch exception")
            pass
        if (isSolMergerInstalled==False):
            print("installing sol-merger...")
            procRetCode=os.system("npm install sol-merger")
            if(procRetCode!=0):
                print("ERROR: failed to install sol-merger")
            else:
                print("sol-merger was installed")

srcContrPathOrig=os.path.realpath(os.path.join(os.path.dirname(sys.argv[0]), 'smartcontracts'))
srcContrPath=os.path.realpath(os.path.join(srcContrPathOrig, '../build'))

buildDir=srcContrPath
contractAddress=''
contractName='MagicChain721'
contractFileName='MagicChain721.sol'
compileOut=os.path.join(buildDir, 'out'+contractName)
addrPath=os.path.join(buildDir, contractName+'Address.txt')

# config for npm to run sol-merger
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

if not os.path.exists('smartcontracts'):
    shutil.copytree('../../smartcontracts', 'smartcontracts')
if not os.path.exists('node_modules/github.com/OpenZeppelin/openzeppelin-contracts'):
    if not os.path.exists(openZeppContracts):
        print("ERROR: specified open zeppelin constract folder does not exist")
        exit(2)
    shutil.copytree(openZeppContracts, 'node_modules/github.com/OpenZeppelin/openzeppelin-contracts')

# run sol-merger to combine contract and its dependencies.
procRetCode=os.system("npm run build-contracts")
if(procRetCode!=0):
    print("ERROR: process retCode!=0.")
    exit(1)

# combined contract deploy
procRetCode=os.system("python3 DeployContract.py {0} {1} {2} {3} {4} {5}"
          .format(srcContrPath+"/"+contractFileName, contractName, compileOut, deployerAddress, addrPath, ipcGethPath))
if(procRetCode!=0):
    print("ERROR: process retCode!=0.")
    exit(1)

try:
    with open(addrPath, 'r') as myfile:
        contractAddress = myfile.read()
except Exception:
    print("Contract is not deployed")
    exit(1)

print("Full deploy success. Contract address={0}".format(contractAddress))
