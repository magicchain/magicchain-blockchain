import json
import sys
import os
import shutil
import re
import subprocess

# import our modules
commonImportDir=os.path.realpath(os.path.join(os.path.dirname(sys.argv[0]), '../Common'))
sys.path.append(commonImportDir)

import EstIpcConnection


helpStr="Use: FullDeploy.py <path of ipc connection to geth> " \
        "<open zeppelin contracts path>='../../../openzeppelin-contracts-master' " \
        "<contract deployer address>=0 " \
        "<install sol-merger locally>=0 (available vals: 0|1). " \
        "Use 0 or omit it (if it is the last param) to set the default parameter."

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

ipcCon = EstIpcConnection.estOnlyConnection(ipcGethPath, False)

deployerAddress='0'
if len(sys.argv)>=4:
    if(sys.argv[3]!='0'):
        deployerAddress=ipcCon.toChecksumAddress(sys.argv[3])

if deployerAddress == "0":
    print("full dep deployer", deployerAddress)
    deployerAddress = ipcCon.eth.coinbase

npmPrefix=''
npmPrefixList=[]
if os.path.dirname(sys.argv[0])!='':
    npmPrefix="{0} {1}".format("--prefix", os.path.dirname(sys.argv[0]))
    npmPrefixList=["--prefix", "{}".format(os.path.dirname(sys.argv[0]))]

if len(sys.argv)>=5:
    if(sys.argv[4]=='1'):
        isSolMergerInstalled=False
        try:
            cmdList=["npm", "list"]
            cmdList.extend(npmPrefixList)
            cmdList.append("sol-merger")
            output = subprocess.check_output(cmdList)
            isSolMergerInstalled=('empty' not in output.decode("utf-8"))
        except Exception:
            print("'npm list sol-merger' catch exception")
            pass
        if (isSolMergerInstalled==False):
            print("installing sol-merger...")
            procRetCode=os.system("npm install {} sol-merger".format(npmPrefix))
            if(procRetCode!=0):
                print("ERROR: failed to install sol-merger")
            else:
                print("sol-merger was installed")
        else:
            print('sol-merger already installed')

srcContrPathOrig=os.path.realpath(os.path.join(os.path.dirname(sys.argv[0]), '../../smartcontracts'))
srcContrPath=os.path.realpath(os.path.join(os.path.dirname(sys.argv[0]), 'build'))
buildDir=srcContrPath

# it is necessary to copy contact files to same dir where sol-merger was installed or child dirs. 
smartcontractDir=os.path.join(os.path.dirname(sys.argv[0]), 'smartcontracts')
if not os.path.exists(smartcontractDir):
    os.makedirs(smartcontractDir)
contractFiles = [curFile for curFile in os.listdir(srcContrPathOrig) if re.search('.sol', curFile)]
for contractFile in contractFiles:
    srcContractFile=os.path.join(srcContrPathOrig, contractFile)
    dstContractFile=os.path.join(smartcontractDir, contractFile)
    if not os.path.exists(dstContractFile):
        print("copy {0}".format(contractFile))
        shutil.copyfile(srcContractFile, dstContractFile)
    else:
        print("{0} has already copied".format(contractFile))

# config for npm to run sol-merger
solMergerPath='sol-merger'
packageData={
"scripts": {
"build-contracts": "{0} \"{1}/*.sol\" \"{2}\"".format(solMergerPath, os.path.realpath(smartcontractDir), buildDir)
},
"devDependencies": {
"sol-merger": "^3.1.0"
}
}

with open(os.path.join(os.path.dirname(sys.argv[0]), 'package.json'), 'w') as myfile:
    json.dump(packageData, myfile)

openzeppelinNodeDir=os.path.join(os.path.dirname(sys.argv[0]), 'node_modules/github.com/OpenZeppelin/openzeppelin-contracts')
if not os.path.exists(openzeppelinNodeDir):
    if not os.path.exists(openZeppContracts):
        print("ERROR: specified open zeppelin constract folder does not exist")
        exit(2)
    shutil.copytree(openZeppContracts, openzeppelinNodeDir)

# run sol-merger to combine contract and its dependencies.
procRetCode=os.system("npm run {0} build-contracts".format(npmPrefix))
if(procRetCode!=0):
    print("ERROR: process retCode!=0.")
    exit(1)

deployContPath=os.path.realpath(os.path.join(os.path.dirname(sys.argv[0]), 'DeployContract.py'))

# combined contract deploy
contractAddress=''
contractName='MagicChain721'
contractFileName='MagicChain721.sol'
compileOutDir=os.path.join(buildDir, 'out'+contractName)
addrPath=os.path.join(buildDir, contractName+'Address.txt')

procRetCode=os.system("python3 {0} {1} {2} {3} {4} {5} {6}"
          .format(deployContPath, srcContrPath+"/"+contractFileName, contractName, compileOutDir, deployerAddress, addrPath, ipcGethPath))
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
