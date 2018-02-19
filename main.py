import time, json, psycopg2
from sys import argv, exit
from block import makeBlock, makeTxn
from checking import checkChain, checkBlockValidity
from hashMe import hashMe
from chain import readChainSql, viewChainSql, writeChainSql
from config import config
from blockpy_logging import logger

def connect():
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        # read connection parameters
        params = config()
 
        # connect to the PostgreSQL server
        print 'Connecting to the PostgreSQL database...'
        logger.info("Connecting to the PostgreSQL database...")
        conn = psycopg2.connect(**params)
 
        # create a cursor
        cur = conn.cursor()
        
        # execute a statement
        print 'PostgreSQL database version:'
        cur.execute('SELECT version()')
 
        # display the PostgreSQL database server version
        db_version = cur.fetchone()
        print(db_version)
        logger.info("PostgreSQL database version: \n%s", db_version)

    except psycopg2.DatabaseError as error:
        print error
        logger.error("Database error", exc_info=True)
    except Exception as error:
        print error
        logger.error("Exception error", exc_info=True)
    finally:
        return conn, cur

def disconnect(conn, cur):
    try:
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        logger.error("Disconnect error", exc_info=True)
    finally:
        if conn is not None:
            conn.close()
            print 'Database connection closed.'
            logger.info("Database connection closed")

def create(message, conn, cur):
    print '\nReading contents of current chain...\n'
    #commented out for simulation purposes
    chain = readChainSql(conn, cur)
    # viewChainSql(chain)
    txnList = []
    for txn in message:
        try:
            txn = json.loads(txn)
        except Exception as error:
            print "Json loads error", error
            logger.error("Json loads error", exc_info=True)
        txn['content'] = json.dumps(txn['content'])
        txnList.append(makeTxn(txn['_owner'], txn['_recipient'], txn['content']))
    newBlock = makeBlock(txnList, chain)
    # print 'newBlock', newBlock['contents']
    logger.info("New block generated",
        extra={"newBlock": newBlock})
    if (checkBlockValidity(newBlock, chain[-1])):
        chain.append(newBlock)
        if (checkChain(chain)):
            print "Chain is valid!"
            logger.info("Chain is valid")
            # viewChainSql(chain)
    return newBlock

def addToChain(newBlock, conn, cur):
    print 'Writing to DB...\n'
    writeChainSql(newBlock, conn, cur)
    logger.info("Database updated")

