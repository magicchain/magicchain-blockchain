import datetime
import time
import math

import web3
import EstIpcConnection

def createUsers(ipcCon: web3.Web3, userCnt: int, addressFileName: str, desciption: str):
    print('create {} {}'.format(userCnt, desciption))
    userList=[]
    tx_hashList=[]
    print(datetime.datetime.now())
    # cамая долгая операция unlockAccount
    for i in range(userCnt):
        userList.append(ipcCon.geth.personal.newAccount('qwerty'))
        ipcCon.geth.personal.unlockAccount(userList[i], 'qwerty', 7*24*3600)
    print(datetime.datetime.now())
    # Транзакции выполняются быстро
    for i in range(userCnt):
        tx={'to': userList[i], 'from': ipcCon.eth.coinbase, 'value': 10000*1000000000000000000, 'gas': 4000000}
        tx_hash = ipcCon.eth.sendTransaction(tx)
        tx_hashList.append(tx_hash)
    # Рецепты Транзакций тоже
    for i in range(userCnt):
        tx_receipt = ipcCon.eth.waitForTransactionReceipt(tx_hashList[i])
        if(tx_receipt.status==0):
            print(ipcCon.debug.TraceTransaction(tx_hashList[i].hex()))
    print(datetime.datetime.now())
    # cохраним адреса инвесторов для последующих тестов.
    with open(addressFileName, 'w') as myfile:
        for item in userList:
            myfile.write("{}\n".format(item))
    print('{} {} created'.format(userCnt, desciption))
    #print('userInvestI1 addr={} balance={}'.format(userInvestI1[i], ipcCon.eth.getBalance(userInvestI1[i])))
    
def loadUserAddrsAll(addressFileName):
    savedAddr=[]
    with open(addressFileName, 'r') as myfile:
        for line in myfile:
            savedAddr.append(line.rstrip('\n'))
    return savedAddr
    
def loadUserAddrs(addressFileName, idx1, idx2):
    savedAddr=[]
    with open(addressFileName, 'r') as myfile:
        for line in myfile:
            savedAddr.append(line.rstrip('\n'))
    if(idx2-idx1==1):
        return savedAddr[idx1]
    else:
        return savedAddr[idx1:idx2]
        
def alignToZeroSec():
    d1=datetime.datetime.now()
    print("Aligner current date {}".format(d1))
    if(d1.second>0):
        time.sleep(60-d1.second)
    print("Aliner date aligned {}".format(datetime.datetime.now()))
    
def startTimer():
    startDateSec=datetime.datetime.now().timestamp()
    timeFile='time.txt'
    print('start timer {}'.format(startDateSec))
    with open(timeFile, 'w') as myfile:
        myfile.write('{}'.format(startDateSec))
    
def waitFor(secondsFromStart):
    nowTs=datetime.datetime.now().timestamp()
    startDateSec=0
    timeFile='time.txt'
    with open(timeFile, 'r') as myfile:
        startDateSec=float(myfile.read())
    waitTime=secondsFromStart-(nowTs-startDateSec)
    if(waitTime<0):
        print('wait for {}'.format(waitFor))
        exit(1)
    print(datetime.datetime.utcfromtimestamp(startDateSec).strftime('%Y-%m-%d %H:%M:%S'), '//' , datetime.datetime.utcfromtimestamp((nowTs+waitTime)).strftime('%Y-%m-%d %H:%M:%S'), '//' ,  waitTime)
    time.sleep(waitTime)
    print("sleep finish {}".format(datetime.datetime.now().timestamp()))
    
def getPassedTime():
    nowTs=datetime.datetime.now().timestamp()
    startDateSec=0
    timeFile='time.txt'
    with open(timeFile, 'r') as myfile:
        startDateSec=float(myfile.read())
    passedTime=nowTs-startDateSec
    print('passed time {}, {}, current time={}'.format(passedTime, passedTime/60, datetime.datetime.utcfromtimestamp(nowTs).strftime('%Y-%m-%d %H:%M:%S')))


class EventUtils:
    @staticmethod
    def toAddressHex(addressStr: str):
        return '0x' + addressStr[2:].rjust(64, '0').lower()

    @staticmethod
    def toIntHex(val: int):
        return "0x{:064x}".format(val)

    @staticmethod
    def toStringHex(strVal: str):
        return '0x' + strVal.ljust(math.ceil(len(strVal)/64)*64, '0')