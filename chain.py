import json, psycopg2, random, string
from datetime import date
from collections import OrderedDict
from hashMe import hashMe

def readChainSql(conn, cur):
    checkIfEmpty(conn, cur)
    queryParentSql = 'SELECT * FROM blocks ORDER BY "block_number" asc'
    chain = []
    try:
        cur.execute(queryParentSql)
        chain = cur.fetchall()
    except psycopg2.ProgrammingError as error:
        print error
    if chain == []:
        g = createGenesisBlockSql(conn, cur)
        queryParentSql = 'SELECT * FROM blocks ORDER BY "block_number" asc'
        cur.execute(queryParentSql)
        chain = cur.fetchall()

    indexes = ['blockNumber', 'blockHash', 'parentHash', 'blockTxn', 'timestamp', 'txnCount']
    newChain = []
    for j in range(len(chain)):
        contents = {indexes[i]: chain[j][i] for i in range(len(chain[j])) if i != 1}
        block = {'blockHash': chain[j][1]}
        block['contents'] = contents
        newChain.append(block)
    return newChain

def checkIfEmpty(conn, cur):
    createTableSql = 'CREATE TABLE IF NOT EXISTS blocks(block_number SERIAL PRIMARY KEY, block_hash VARCHAR(255) NOT NULL, parent_hash VARCHAR(255), block_txn VARCHAR(255), timestamp TIMESTAMP, txn_count INTEGER)'
    cur.execute(createTableSql)
    conn.commit()

def createGenesisBlockSql(conn, cur):
    genesisBlockSql = 'INSERT INTO blocks("block_hash") VALUES (%s)'
    r = 'b72c1d29818ac5daca49b033af50f3babd94bab802c51d4896d40a82950290ed'
    cur.execute(genesisBlockSql, (r,))
    conn.commit()
    return r

def viewChainSql(chain):
    for block in chain:
        blockHash = block['blockHash']
        hashLen = len(blockHash)
        blockTxn = block['contents']['blockTxn']
        blockNumberFormatted = '| BlockNumber: ' + str(block['contents']['blockNumber'])
        print ('=' * (hashLen+4))
        print blockNumberFormatted + ' ' * (hashLen - len(blockNumberFormatted) + 2) + ' |'
        print ('=' * (hashLen+4))
        print '|' + ' ' * ((hashLen/2)-1) + 'hash' + ' ' * ((hashLen/2)-1) + '|'
        print '| ' + block['blockHash'] + ' |'
        print '|' + ' ' * (hashLen+2) + '|'
        print '|' + ' ' * ((hashLen/2)-3) + 'blockTxn' + ' ' * ((hashLen/2)-3 ) + '|'
        print '| ' + (blockTxn if (blockTxn != None) else ' ' * ((hashLen/2)-2) + 'NULL' + ' ' * ((hashLen/2)-2)) + ' |'
        print ('=' * (hashLen+4))
        print (' ' * (hashLen/2)) + '  |'

def writeChainSql(block, conn, cur):
    insertSql = '''INSERT INTO blocks("block_hash", "parent_hash", "block_txn", "timestamp", "txn_count")
        VALUES(%s, %s, %s, %s, %s) RETURNING "block_number";'''
    contents = block['contents']
    cur.execute(insertSql, (block['blockHash'], contents['parentHash'], contents['blockTxn'], contents['timestamp'], contents['txnCount']))
    blockNumber = cur.fetchone()[0]
    # if blockNumber == contents['blockNumber']:
    #     print "Block Numbers match!"
    conn.commit()