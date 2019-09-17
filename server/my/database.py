#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

import collections
import time


DepositAddress=collections.namedtuple("DepositAddress", ["coin", "userid", "status", "txuuid", "address", "extra"])
ETHTransaction=collections.namedtuple("ETHTransaction", ["uuid", "chainid", "creationTime", "sendTime", "status", "sender", "receiver", "value", "gasLimit", "gasPrice", "nonce", "data", "txhash"])
Deposit=collections.namedtuple("Deposit", ["coin", "txid", "vout", "notified", "blockNumber", "userid", "amount", "tokenId"])

class DatabaseConnectionFactory:
    @staticmethod
    def connect(config):
        driver=config.pop("driver", "mysql")
        if driver=="mysql":
            return MysqlDatabaseConnection(**config)
        else:
            raise ValueError("Unsupported database driver {}".format(driver))

class MysqlDatabaseConnection:
    currentDatabaseVersion=1

    def __init__(self, *, host, user, password, dbname):
        import pymysql
        self.db=pymysql.connect(host=host, user=user, passwd=password, db=dbname)
        self.db.cursor().execute("SET sql_notes = 0;")
        self.db.cursor().execute("""CREATE TABLE IF NOT EXISTS dbVersion
            (
                fake INT NOT NULL,
                version INT NOT NULL,
                PRIMARY KEY(fake)
            );""")

        self.db.cursor().execute("""CREATE TABLE IF NOT EXISTS depositAddresses
            (
                coin VARCHAR(30) NOT NULL,
                userid BIGINT UNSIGNED NOT NULL,
                status INT NOT NULL,
                txuuid VARCHAR(36) DEFAULT NULL,
                address VARCHAR(100) DEFAULT NULL,
                extra1name VARCHAR(20) DEFAULT NULL,
                extra1value VARCHAR(32) DEFAULT NULL,
                extra2name VARCHAR(20) DEFAULT NULL,
                extra2value VARCHAR(32) DEFAULT NULL,
                PRIMARY KEY(coin, userid)
            );""")

        self.db.cursor().execute("""CREATE TABLE IF NOT EXISTS ethTransactions
            (
                uuid VARCHAR(36) NOT NULL,
                chainid VARCHAR(20) NOT NULL,
                creationTime BIGINT UNSIGNED NOT NULL,
                sendTime BIGINT UNSIGNED,
                status INT NOT NULL,
                sender VARCHAR(42) NOT NULL,
                receiver VARCHAR(42) NOT NULL,
                value VARCHAR(66) NOT NULL,
                gasLimit VARCHAR(66) DEFAULT NULL,
                gasPrice VARCHAR(66) DEFAULT NULL,
                nonce VARCHAR(66) DEFAULT NULL,
                data BLOB NOT NULL,
                txhash VARCHAR(66) DEFAULT NULL,
                PRIMARY KEY(uuid)
            );""")

        self.db.cursor().execute("""CREATE TABLE IF NOT EXISTS depositTransactions
            (
                coin VARCHAR(30) NOT NULL,
                txid VARCHAR(80) NOT NULL,
                vout BIGINT UNSIGNED NOT NULL,
                notified TINYINT NOT NULL,
                blockNumber BIGINT UNSIGNED NOT NULL,
                userid BIGINT UNSIGNED,
                amount VARCHAR(66),
                tokenId VARCHAR(66),
                PRIMARY KEY(coin, txid, vout)
            );""")

        self.db.cursor().execute("""CREATE TABLE IF NOT EXISTS lastScannedBlock
            (
                coin VARCHAR(30) NOT NULL,
                blockNumber BIGINT UNSIGNED NOT NULL,
                PRIMARY KEY(coin)
            );""")

        self.db.cursor().execute("""CREATE TABLE IF NOT EXISTS ethPrivateKeys
            (
                address VARCHAR(42) NOT NULL,
                privateKey VARCHAR(64) NOT NULL,
                PRIMARY KEY(address)
            );""")

        self.db.cursor().execute("INSERT IGNORE INTO dbVersion SET fake=0, version=%s;", (self.currentDatabaseVersion,))

        self.db.cursor().execute("SET sql_notes = 1;")
        self.db.commit()

        if self.__getDatabaseVersion()<1: self.__migrate_0to1()
        #if self.__getDatabaseVersion()<2: self.__migrate_1to2()
        #if self.__getDatabaseVersion()<3: self.__migrate_2to3()
        assert self.__getDatabaseVersion()==self.currentDatabaseVersion

    def getExistingDepositAddress(self, *, coin, userid):
        cur=self.db.cursor()
        if cur.execute("SELECT * FROM depositAddresses WHERE coin=%s AND userid=%s AND status=0;", (coin, userid))==0:
            return None

        return MysqlDatabaseConnection.__tupleToDepositAddress(cur.fetchone())

    def addDepositAddressRequest(self, *, coin, userid):
        self.db.cursor().execute("INSERT IGNORE INTO depositAddresses SET coin=%s, userid=%s, status=1;", (coin, userid))
        self.db.commit()

    def getPendingDepositAddressRequests(self):
        cur=self.db.cursor()
        cur.execute("SELECT * FROM depositAddresses WHERE status>0;")

        for t in cur.fetchall():
            yield MysqlDatabaseConnection.__tupleToDepositAddress(t)

    def getDepositAddressRequest(self, *, coin, userid):
        cur=self.db.cursor()
        if cur.execute("SELECT * FROM depositAddresses WHERE coin=%s AND userid=%s;", (coin, userid))==0:
            return None

        return MysqlDatabaseConnection.__tupleToDepositAddress(cur.fetchone())

    def updateDepositAddress(self, *, coin, userid, **kwargs):
        exprs=[]
        args=dict(coin=coin, userid=userid)

        for name in ("status", "txuuid", "address"):
            if name in kwargs:
                exprs.append(name+"=%("+name+")s")
                args[name]=kwargs[name]
        if "extra" in kwargs:
            extra=kwargs["extra"]
            if not isinstance(extra, dict) or len(extra)>2:
                raise TypeError('"extra" must be a dictionary with at most 2 keys')
            extra=extra.items()

            exprs.append("extra1name=%(extra1name)")
            exprs.append("extra1value=%(extra1value)")
            exprs.append("extra2name=%(extra2name)")
            exprs.append("extra2value=%(extra2value)")

            args["extra1name"]=extra[0][0] if len(extra)>0 else None
            args["extra1value"]=extra[0][1] if len(extra)>0 else None
            args["extra2name"]=extra[1][0] if len(extra)>1 else None
            args["extra2value"]=extra[1][1] if len(extra)>1 else None

        self.db.cursor().execute("UPDATE depositAddresses SET "+", ".join(exprs)+" WHERE coin=%(coin)s AND userid=%(userid)s;", args)
        self.db.commit()

    def addPendingTransaction(self, *, uuid, chainid, sender, receiver, value, data):
        self.db.cursor().execute(
            "INSERT IGNORE INTO ethTransactions SET uuid=%(uuid)s, chainid=%(chainid)s, creationTime=%(ctime)s, sendTime=NULL, status=1, sender=%(sender)s, receiver=%(receiver)s, value=%(value)s, data=%(data)s;",
            dict(
                uuid=uuid,
                chainid=chainid,
                ctime=int(time.time()),
                sender=sender,
                receiver=receiver,
                value="0x{:x}".format(value),
                data=data))
        self.db.commit()

    def getTransaction(self, uuid):
        cur=self.db.cursor()
        if cur.execute("SELECT * FROM ethTransactions WHERE uuid=%s;", (uuid,))==0:
            return None

        return MysqlDatabaseConnection.__tupleToTransaction(cur.fetchone())

    def getPendingTransactions(self):
        cur=self.db.cursor()
        cur.execute("SELECT * FROM ethTransactions WHERE status>0;")

        for t in cur.fetchall():
            yield MysqlDatabaseConnection.__tupleToTransaction(t)

    def findHighestNonce(self, *, sender):
        with self.db.cursor() as cur:
            # This wouldn't work since nonce is the database is stored as hex
            # cur.execute("SELECT MAX(nonce) FROM ethTransactions WHERE sender=%s AND nonce IS NOT NULL;", (sender,))
            # return cur.fetchone()[0]

            if cur.execute("SELECT nonce FROM ethTransactions WHERE sender=%s AND nonce IS NOT NULL AND status>=2;", (sender,))==0:
                return None

            return max((int(nonce, 16) for (nonce,) in cur.fetchall()))

    def updateTransaction(self, *, uuid, **kwargs):
        exprs=[]
        args=dict(uuid=uuid)

        for name in ("sendTime", "status", "txhash"):
            if name in kwargs:
                exprs.append(name+"=%("+name+")s")
                args[name]=kwargs[name]
        for name in ("gasPrice", "gasLimit", "nonce"):
            if name in kwargs:
                exprs.append(name+"=%("+name+")s")
                args[name]="0x{:x}".format(kwargs[name])

        self.db.cursor().execute("UPDATE ethTransactions SET "+", ".join(exprs)+" WHERE uuid=%(uuid)s;", args)
        self.db.commit()

    def addNewDeposit(self, *, coin, txid, vout, blockNumber, userid, amount, tokenId):
        self.db.cursor().execute(
            "INSERT IGNORE INTO depositTransactions SET coin=%(coin)s, txid=%(txid)s, vout=%(vout)s, notified=0, blockNumber=%(blockNumber)s, userid=%(userid)s, amount=%(amount)s, tokenId=%(tokenId)s;",
            dict(
                coin=coin,
                txid=txid,
                vout=vout,
                blockNumber=blockNumber,
                userid=userid,
                amount=amount,
                tokenId=tokenId))
        self.db.commit()

    def updateDeposit(self, *, coin, txid, vout, notified):
        self.db.cursor().execute(
            "UPDATE depositTransactions SET notified=%(notified)s WHERE coin=%(coin)s AND txid=%(txid)s AND vout=%(vout)s;",
            dict(
                coin=coin,
                txid=txid,
                vout=vout,
                notified=int(notified)))
        self.db.commit()

    def getLastScannedBlock(self, *, coin):
        cur=self.db.cursor()
        if cur.execute("SELECT blockNumber FROM lastScannedBlock WHERE coin=%s;", (coin,))==0:
            return None

        return cur.fetchone()[0]

    def setLastScannedBlock(self, *, coin, blockNumber):
        self.db.cursor().execute(
            "INSERT INTO lastScannedBlock SET coin=%(coin)s, blockNumber=%(blockNumber)s ON DUPLICATE KEY UPDATE blockNumber=%(blockNumber)s;",
            dict(
                coin=coin,
                blockNumber=blockNumber))
        self.db.commit()

    def getPendingDeposits(self):
        cur=self.db.cursor()
        cur.execute("SELECT * FROM depositTransactions WHERE notified=0;")

        for t in cur.fetchall():
            yield MysqlDatabaseConnection.__tupleToDeposit(t)

    def getPrivateKey(self, address):
        cur=self.db.cursor()
        if cur.execute("SELECT privateKey FROM ethPrivateKeys WHERE address=%s;", (address,))==0:
            return None

        return bytes.fromhex(cur.fetchone()[0])

    def storePrivateKey(self, address, privateKey):
        self.db.cursor().execute("INSERT IGNORE INTO ethPrivateKeys SET address=%s, privateKey=%s;", (address, privateKey.hex()));
        self.db.commit()

    @staticmethod
    def __tupleToDepositAddress(t):
        coin, userid, status, txuuid, address, extra1name, extra1value, extra2name, extra2value=t
        extra={}
        if extra1name is not None:
            extra[extra1name]=extra1value
        if extra2name is not None:
            extra[extra2name]=extra2value

        return DepositAddress(coin, userid, status, txuuid, address, extra)

    @staticmethod
    def __tupleToTransaction(t):
        uuid, chainid, creationTime, sendTime, status, sender, receiver, value, gasLimit, gasPrice, nonce, data, txhash=t
        return ETHTransaction(
            uuid,
            chainid,
            creationTime,
            sendTime,
            status,
            sender,
            receiver,
            int(value, 16),
            None if gasLimit is None else int(gasLimit, 16),
            None if gasPrice is None else int(gasPrice, 16),
            None if nonce is None else int(nonce, 16),
            data,
            txhash)

    @staticmethod
    def __tupleToDeposit(t):
        coin, txid, vout, notified, blockNumber, userid, amount, tokenId=t
        return Deposit(
            coin,
            txid,
            vout,
            notified,
            blockNumber,
            userid,
            int(amount, 0),
            tokenId)

    def __getDatabaseVersion(self):
        with self.db.cursor() as cur:
            cur.execute("SELECT version FROM dbVersion WHERE fake=0;")
            return cur.fetchone()[0]

    def __migrate_0to1(self):
        # v0->v1 - new status codes were introduced, so convert them. Some fields' definition
        # has changed (DEFAULT NULL instead of NOT NULL).

        self.db.cursor().execute("""ALTER TABLE ethTransactions
                                        CHANGE gasLimit gasLimit VARCHAR(66) DEFAULT NULL,
                                        CHANGE gasPrice gasPrice VARCHAR(66) DEFAULT NULL,
                                        CHANGE nonce nonce VARCHAR(66) DEFAULT NULL,
                                        CHANGE txhash txhash VARCHAR(66) DEFAULT NULL;
                                 """)

        self.db.cursor().execute("UPDATE ethTransactions SET status=5 WHEREstatus=3;")
        self.db.cursor().execute("UPDATE ethTransactions SET status=1 WHEREstatus=2;")
        self.db.cursor().execute("UPDATE ethTransactions SET nonce=NULL, gasPrice=NULL, gasLimit=NULL;")
        self.db.cursor().execute("UPDATE dbVersion SET version=1 WHERE fake=0;")
        self.db.commit()
