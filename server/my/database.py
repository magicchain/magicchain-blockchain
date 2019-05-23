#! /usr/bin/env python3
# Blashyrkh.maniac.coding
# BTC:1Maniaccv5vSQVuwrmRtfazhf2WsUJ1KyD DOGE:DManiac9Gk31A4vLw9fLN9jVDFAQZc2zPj

import collections
import time


class DatabaseConnectionFactory:
    @staticmethod
    def connect(config):
        driver=config.pop("driver", "mysql")
        if driver=="mysql":
            return MysqlDatabaseConnection(**config)
        else:
            raise ValueError("Unsupported database driver {}".format(driver))

class MysqlDatabaseConnection:
    DepositAddress=collections.namedtuple("DepositAddress", ["coin", "userid", "status", "txuuid", "address", "extra"])
    ETHTransaction=collections.namedtuple("ETHTransaction", ["uuid", "chainid", "creationTime", "sendTime", "status", "sender", "receiver", "value", "gasLimit", "gasPrice", "nonce", "data", "txhash"])

    def __init__(self, *, host, user, password, dbname):
        import pymysql
        self.db=pymysql.connect(host=host, user=user, passwd=password, db=dbname)
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
                gasLimit VARCHAR(66) NOT NULL,
                gasPrice VARCHAR(66) NOT NULL,
                nonce VARCHAR(66) NOT NULL,
                data VARCHAR(288) NOT NULL,
                txhash VARCHAR(66),
                PRIMARY KEY(uuid, chainid)
            );""")


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
            yield(MysqlDatabaseConnection.__tupleToDepositAddress(t))

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
            "INSERT IGNORE INTO ethTransactions SET uuid=%(uuid)s, chainid=%(chainid)s, creationTime=%(ctime)s, sendTime=NULL, status=1, sender=%(sender)s, receiver=%(receiver)s, value=%(value)s, gasLimit='0x0', gasPrice='0x0', nonce='0x0', data=%(data)s, txhash=NULL;",
            dict(
                uuid=uuid,
                chainid=chainid,
                ctime=int(time.time()),
                sender=sender,
                receiver=receiver,
                value="0x{:x}".format(value),
                data="0x"+data.hex()))
        self.db.commit()

    def getTransaction(self, *, uuid, chainid):
        cur=self.db.cursor()
        if cur.execute("SELECT * FROM ethTransactions WHERE uuid=%(uuid)s AND chainid=%(chainid)s;", dict(uuid=uuid, chainid=chainid))==0:
            return None

        uuid, chainid, creationTime, sendTime, status, sender, receiver, value, gasLimit, gasPrice, nonce, data, txhash=cur.fetchone()
        return MysqlDatabaseConnection.ETHTransaction(
            uuid,
            chainid,
            creationTime,
            sendTime,
            status,
            sender,
            receiver,
            int(value, 16),
            int(gasLimit, 16),
            int(gasPrice, 16),
            int(nonce, 16),
            bytes.fromhex(data[2:]),
            txhash)

    @staticmethod
    def __tupleToDepositAddress(t):
        coin, userid, status, txuuid, address, extra1name, extra1value, extra2name, extra2value=t
        extra={}
        if extra1name is not None:
            extra[extra1name]=extra1value
        if extra2name is not None:
            extra[extra2name]=extra2value

        return MysqlDatabaseConnection.DepositAddress(coin, userid, status, txuuid, address, extra)