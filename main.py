import time, json, psycopg2
from sys import argv, exit
from block import makeBlock, makeTxn
from checking import checkChain, checkBlockValidity
from hashMe import hashMe
from chain import readChainSql, viewChainSql, writeChainSql
from config import config

def connect():
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        # read connection parameters
        params = config()
 
        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)
 
        # create a cursor
        cur = conn.cursor()
        
        # execute a statement
        print('PostgreSQL database version:')
        cur.execute('SELECT version()')
 
        # display the PostgreSQL database server version
        db_version = cur.fetchone()
        print(db_version)

    except psycopg2.DatabaseError as error:
        print error
    except Exception as error:
        print error
    finally:
        return conn, cur

def disconnect(conn, cur):
    try:
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')

def create(message, conn, cur):
    print '\nReading contents of current chain...\n'
    chain = readChainSql(conn, cur)
    viewChainSql(chain)
    txnList = []
    for txn in message:
        try:
            txn = json.loads(txn)
        except Exception as error:
            print "JSONLOADSERROR", error
        print txn
        txn['content'] = json.dumps(txn['content'])
        txnList.append(makeTxn(txn['_owner'], txn['_recipient'], txn['content']))
    newBlock = makeBlock(txnList, chain)
    print 'newBlock', newBlock['contents']
    if (checkBlockValidity(newBlock, chain[-1])):
        chain.append(newBlock)
        print chain
        if (checkChain(chain)):
            print "Chain is valid!"
            viewChainSql(chain)
    return newBlock

def addToChain(newBlock, conn, cur):
    print 'Writing to DB...\n'
    writeChainSql(newBlock, conn, cur)

