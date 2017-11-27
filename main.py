import time, json, py2p, psycopg2
from sys import argv, exit
from block import makeBlock, makeTxn
from checking import checkChain, checkBlockValidity
from hashMe import hashMe
from chain import readChain, viewChain, writeChain, readChainSql, viewChainSql, writeChainSql
from config import config

# Create Mesh Socket at port 4444
sock = py2p.MeshSocket('0.0.0.0', 4444)
maxTxns = 1
blockLocation = 'JSON/Chain.json'

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
       
        # close the communication with the PostgreSQL
        # cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
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


def main():
    [cur, conn] = connect()
    print '\nReading contents of current chain...\n'
    # readChain(blockLocation)
    chain = readChainSql(cur)
    # viewChain(chain)
    viewChainSql(chain)
    while True:
        msg = sock.recv()

        txnList = []
        if (msg and msg.packets[1:]):
            print msg
            packet = msg.packets[1]
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
                if (checkChain(chain)):
                    viewChainSql(chain)
                    print 'Writing to file...\n'
                    writeChainSql(newBlock, conn, cur)
                    # writeChain(chain, blockLocation)
    disconnect(conn, cur)

if __name__ == '__main__':
    main()





