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
        return [cur, conn]

def disconnect(conn, cur):
    try:
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')


def create(packet = None):
    b = packet
    [cur, conn] = connect()
    print '\nReading contents of current chain...\n'
    chain = readChainSql(conn, cur)
    msg = None
    viewChainSql(chain)
    while True:
        if not packet:
            msg = sock.recv()

        txnList = []
        if (msg and msg.packets[1:] and not packet) or packet:
            if not packet:
                packet = msg.packets[1]
            print packet
            try:
                txn = json.loads(packet)
            except:
                txn = packet
            txn['content'] = hashMe(json.dumps(txn['content']))
            txnList.append(makeTxn(txn['_owner'], txn['_recipient'], txn['content']))
            print 'Done Receiving\n'
            newBlock = makeBlock(txnList, chain)
            if (checkBlockValidity(newBlock, chain[-1])):
                txnList.pop()
                chain.append(newBlock)
                print chain
                if (checkChain(chain)):
                    viewChainSql(chain)
                    print 'Writing to file...\n'
                    writeChainSql(newBlock, conn, cur)
                    # writeChain(chain, blockLocation)
        if b:
            break
    disconnect(conn, cur)

