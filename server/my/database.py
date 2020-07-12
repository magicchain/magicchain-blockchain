#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

import collections
import time


DepositAddress=collections.namedtuple("DepositAddress", ["coin", "userid", "status", "txuuid", "address", "extra"])
ETHTransaction=collections.namedtuple("ETHTransaction", ["uuid", "chainid", "creationTime", "sendTime", "status", "sender", "receiver", "value", "gasLimit", "gasPrice", "nonce", "data", "customResultHandler", "txhash", "result"])
Deposit=collections.namedtuple("Deposit", ["no", "coin", "txid", "vout", "blockNumber", "userid", "amount", "tokenId", "tokenContent"])

class DatabaseConnectionFactory:
    @staticmethod
    def connect(config):
        driver=config.pop("driver", "mysql")
        if driver=="mysql":
            return MysqlDatabaseConnection(**config)
        else:
            raise ValueError("Unsupported database driver {}".format(driver))

class MysqlDatabaseConnection:
    currentDatabaseVersion=3

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
                customResultHandler VARCHAR(20) DEFAULT NULL,
                txhash VARCHAR(66) DEFAULT NULL,
                PRIMARY KEY(uuid)
            );""")

        self.db.cursor().execute("""CREATE TABLE IF NOT EXISTS ethResults
            (
                uuid VARCHAR(36) NOT NULL,
                name VARCHAR(20) NOT NULL,
                value VARCHAR(66),
                PRIMARY KEY(uuid, name)
            );""")

        self.db.cursor().execute("""CREATE TABLE IF NOT EXISTS depositTransactions
            (
                no BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
                coin VARCHAR(30) NOT NULL,
                txid VARCHAR(80) NOT NULL,
                vout BIGINT UNSIGNED NOT NULL,
                blockNumber BIGINT UNSIGNED NOT NULL,
                userid BIGINT UNSIGNED,
                amount VARCHAR(66),
                tokenId VARCHAR(66),
                content1 VARCHAR(66),
                content2 VARCHAR(66),
                content3 VARCHAR(66),
                content4 VARCHAR(66),
                content5 VARCHAR(66),
                PRIMARY KEY(no),
                UNIQUE INDEX(coin, txid, vout)
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
        if self.__getDatabaseVersion()<2: self.__migrate_1to2()
        if self.__getDatabaseVersion()<3: self.__migrate_2to3()
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

    def addPendingTransaction(self, *, uuid, chainid, sender, receiver, value, data, customResultHandler=None):
        self.db.cursor().execute(
            """INSERT IGNORE INTO ethTransactions
            SET uuid=%(uuid)s,
                chainid=%(chainid)s,
                creationTime=%(ctime)s,
                sendTime=NULL,
                status=1,
                sender=%(sender)s,
                receiver=%(receiver)s,
                value=%(value)s,
                data=%(data)s,
                customResultHandler=%(crh)s;
            """,
            dict(
                uuid=uuid,
                chainid=chainid,
                ctime=int(time.time()),
                sender=sender,
                receiver=receiver,
                value="0x{:x}".format(value),
                data=data,
                crh=customResultHandler))
        self.db.commit()

    def getTransaction(self, uuid):
        cur=self.db.cursor()
        if cur.execute("SELECT * FROM ethTransactions WHERE uuid=%s;", (uuid,))==0:
            return None
        t=cur.fetchone()

        cur.execute("SELECT name, value FROM ethResults WHERE uuid=%s;", (uuid,))
        r=dict(cur.fetchall())

        return MysqlDatabaseConnection.__tupleToTransaction((*t, r))

    def getPendingTransactions(self):
        cur=self.db.cursor()
        cur.execute("SELECT * FROM ethTransactions WHERE status>0;")

        for t in cur.fetchall():
            yield MysqlDatabaseConnection.__tupleToTransaction((*t, {}))

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
        if "result" in kwargs:
            self.db.cursor().execute("DELETE FROM ethResults WHERE uuid=%s;", (uuid,))
            for name, value in kwargs["result"].items():
                self.db.cursor().execute("INSERT INTO ethResults SET uuid=%s, name=%s, value=%s;", (uuid, name, value))
        self.db.commit()

    def addNewDeposit(self, *, coin, txid, vout, blockNumber, userid, amount, tokenId, tokenContent):
        assert tokenContent is None or (isinstance(tokenContent, list) and len(tokenContent)==5)

        if tokenContent is None:
            tokenContent=[None, None, None, None, None]

        self.db.cursor().execute(
            """INSERT INTO depositTransactions
            VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            blockNumber=blockNumber;""",
            (coin, txid, vout, blockNumber, userid, amount, tokenId, tokenContent[0], tokenContent[1], tokenContent[2], tokenContent[3], tokenContent[4]))
        self.db.commit()

    def listDeposits(self, start, limit):
        with self.db.cursor() as cur:
            cur.execute(
                "SELECT * FROM depositTransactions WHERE no>=%s ORDER BY no LIMIT %s;",
                (start, limit))

            return map(self.__tupleToDeposit, cur.fetchall())

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
        uuid, chainid, creationTime, sendTime, status, sender, receiver, value, gasLimit, gasPrice, nonce, data, customResultHandler, txhash, result=t
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
            customResultHandler,
            txhash,
            result)

    @staticmethod
    def __tupleToDeposit(t):
        no, coin, txid, vout, blockNumber, userid, amount, tokenId, tokenContent1, tokenContent2, tokenContent3, tokenContent4, tokenContent5=t
        tokenContent=[tokenContent1, tokenContent2, tokenContent3, tokenContent4, tokenContent5]
        if tokenContent==[None, None, None, None, None]:
            tokenContent=None
        return Deposit(
            no,
            coin,
            txid,
            vout,
            blockNumber,
            userid,
            amount,
            tokenId,
            tokenContent)

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

        self.db.cursor().execute("UPDATE ethTransactions SET status=5 WHERE status=3;")
        self.db.cursor().execute("UPDATE ethTransactions SET status=1 WHERE status=2;")
        self.db.cursor().execute("UPDATE ethTransactions SET nonce=NULL, gasPrice=NULL, gasLimit=NULL;")
        self.db.cursor().execute("UPDATE dbVersion SET version=1 WHERE fake=0;")
        self.db.commit()

    def __migrate_1to2(self):
        # v1->v2 - copy all txhashes from "ethTransactions" table to "ethResults" table,
        # add "customResultHandler" column

        self.db.cursor().execute("""INSERT IGNORE INTO ethResults
                                    SELECT uuid, 'txhash' AS name, txhash AS value
                                    FROM ethTransactions
                                    WHERE status=0;
                                 """)

        self.db.cursor().execute("""ALTER TABLE ethTransactions
                                    ADD customResultHandler VARCHAR(20) DEFAULT NULL AFTER data;
                                 """)

        self.db.cursor().execute("UPDATE dbVersion SET version=2 WHERE fake=0;")
        self.db.commit()

    def __migrate_2to3(self):
        # v2->v3 - change "depositTransactions" table entirely, drop old data

        self.db.cursor().execute("DROP TABLE depositTransactions;")

        self.db.cursor().execute("""CREATE TABLE IF NOT EXISTS depositTransactions
            (
                no BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
                coin VARCHAR(30) NOT NULL,
                txid VARCHAR(80) NOT NULL,
                vout BIGINT UNSIGNED NOT NULL,
                blockNumber BIGINT UNSIGNED NOT NULL,
                userid BIGINT UNSIGNED,
                amount VARCHAR(66),
                tokenId VARCHAR(66),
                content1 VARCHAR(66),
                content2 VARCHAR(66),
                content3 VARCHAR(66),
                content4 VARCHAR(66),
                content5 VARCHAR(66),
                PRIMARY KEY(no),
                UNIQUE INDEX(coin, txid, vout)
            );""")

        self.db.cursor().execute("DELETE FROM lastScannedBlock;")

        self.db.cursor().execute("UPDATE dbVersion SET version=3 WHERE fake=0;")
        self.db.commit()
