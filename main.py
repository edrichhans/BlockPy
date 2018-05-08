import time, json, psycopg2
from sys import argv, exit
from block import makeBlock, makeTxn, createMerkle
from checking import checkChain, checkBlockValidity
from hashMe import hashMe
from chain import readChainSql, viewChainSql, writeChainSql, writeTxnsSql
from config import config
from blockpy_logging import logger

def connect():
    """ Connect to the PostgreSQL database server """
    conn, cur = None, None
    while 1:
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
            break

        except psycopg2.DatabaseError as error:
            print error, 'trying again1...'
            logger.error("Database error", exc_info=True)
            time.sleep(2)
        except Exception as error:
            print error, 'trying again2...'
            logger.error("Exception error", exc_info=True)
            time.sleep(2)

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

def create(messages, conn, cur):
    print '\nReading contents of current chain...\n'
    #commented out for simulation purposes
    chain = readChainSql(conn, cur)
    # viewChainSql(chain)
    txnList = []
    for txn in messages:
        try:
            txn = json.loads(txn)
        except Exception as error:
            print "Json loads error", error
            logger.error("Json loads error", exc_info=True)
        txn['content'] = json.dumps(txn['content'])
        txnList.append(makeTxn(txn['_owner'], txn['_recipient'], txn['content']))
    newBlock = makeBlock(txnList, chain)

    if (checkBlockValidity(newBlock, chain[-1])):
        chain.append(newBlock)
        if (checkChain(chain)):
            print "Chain is valid!"
            logger.info("Chain is valid")
            # viewChainSql(chain)
    return newBlock, txnList

def addToChain(newBlock, conn, cur):
    print 'Writing to Blockchain Table...\n'
    if newBlock:
        blockNumber = writeChainSql(newBlock, conn, cur)
        logger.info("blocks table updated")
    else:
        blockNumber = -1
    return blockNumber

def addToTxns(txns, conn, cur, blockNumber, txnNumber=None, timestamp=None):
    print 'Writing to Txns Table...\n'
    if txns and blockNumber:
        writeTxnsSql(txns, conn, cur, blockNumber, txnNumber, timestamp)
        logger.info("txns table updated")

def verifyTxn(txn, conn, cur):
    getTxnsSql = '''SELECT txn_content FROM txns WHERE
        block_number = (SELECT block_number from txns WHERE
        txn_number = %s);'''
    cur.execute(getTxnsSql, (txn,))
    txns = [i[0] for i in cur.fetchall()]

    getBlockSql = '''SELECT block_txn FROM blocks WHERE
        block_number = (SELECT block_number from txns WHERE
        txn_number = %s);'''
    cur.execute(getBlockSql, (txn,))
    blockMerkle = cur.fetchone()[0]

    generatedMerkle = createMerkle(txns)

    if generatedMerkle != blockMerkle:
        logger.warn('Generated Merkle does not match contents of block. Generated Merkle: %s. Expected: %s',
                generatedMerkle, blockMerkle)
        # raise Exception('Generated Merkle does not match contents of block. Generated Merkle: %s. Expected: %s'%
        #         (generatedMerkle, blockMerkle))
        return False
    return True





