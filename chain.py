import json, psycopg2, random, string, re
from datetime import date, datetime
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

def readTxnsSql(conn, cur):
    checkIfEmpty(conn, cur)
    queryParentSql = 'SELECT * FROM txns ORDER BY "txn_number" asc'
    txns = []
    try:
        cur.execute(queryParentSql)
        txns = cur.fetchall()
    except psycopg2.ProgrammingError as error:
        print error

    indexes = ['txnNumber', 'content', 'blockNumber', 'timestamp']
    newTxns = []
    for j in range(len(txns)):
        txn = {indexes[i]: txns[j][i] for i in range(len(txns[j]))}
        newTxns.append(txn)
    return newTxns

def checkIfEmpty(conn, cur):
    createTableSql = 'CREATE TABLE IF NOT EXISTS blocks(block_number SERIAL PRIMARY KEY, block_hash TEXT NOT NULL, parent_hash TEXT, block_txn TEXT, timestamp TIMESTAMP, txn_count INTEGER);'
    createTableSql += 'CREATE TABLE IF NOT EXISTS txns(txn_number SERIAL NOT NULL PRIMARY KEY, txn_content json NOT NULL, block_number INTEGER NOT NULL, timestamp TIMESTAMP NOT NULL);'
    cur.execute(createTableSql)
    conn.commit()

def createGenesisBlockSql(conn, cur):
    checkIfEmpty(conn, cur)
    genesisBlockSql = 'INSERT INTO blocks("block_hash") SELECT (%s) WHERE NOT EXISTS (SELECT * FROM blocks)'
    r = 'b72c1d29818ac5daca49b033af50f3babd94bab802c51d4896d40a82950290ed'
    cur.execute(genesisBlockSql, (r,))
    conn.commit()
    return r

def viewChainSql(chain):
    for block in chain:
        blockHash = block['blockHash']
        hashLen = len(blockHash)
        blockTxn = str(block['contents']['blockTxn'])
        blockNumberFormatted = '| BlockNumber: ' + str(block['contents']['blockNumber'])
        print ('=' * (hashLen+4))
        print blockNumberFormatted + ' ' * (hashLen - len(blockNumberFormatted) + 2) + ' |'
        print ('=' * (hashLen+4))
        print '|' + ' ' * ((hashLen/2)-1) + 'hash' + ' ' * ((hashLen/2)-1) + '|'
        print '| ' + block['blockHash'] + ' |'
        print '|' + ' ' * (hashLen+2) + '|'
        print '|' + ' ' * ((hashLen/2)-3) + 'blockTxn' + ' ' * ((hashLen/2)-3 ) + '|'
        print '| ' + (re.sub("(.{hashLen})", " |\\1\n| ", blockTxn, 0, re.DOTALL) if (blockTxn != None) else ' ' * ((hashLen/2)-2) + 'NULL' + ' ' * ((hashLen/2)-2)) + ' |'
        print ('=' * (hashLen+4))
        print (' ' * (hashLen/2)) + '  |'

def writeChainSql(block, conn, cur):
    createGenesisBlockSql(conn, cur)
    insertSql = '''INSERT INTO blocks("block_hash", "parent_hash", "block_txn", "timestamp", "txn_count")
        VALUES(%s, %s, %s, %s, %s) RETURNING "block_number";'''
    contents = block['contents']
    cur.execute(insertSql, (block['blockHash'], contents['parentHash'], contents['blockTxn'], contents['timestamp'], contents['txnCount']))
    blockNumber = cur.fetchone()[0]
    conn.commit()
    return blockNumber

def writeTxnsSql(messages, conn, cur, blockNumber, txnNumber=None, timestamp=None):
    checkIfEmpty(conn, cur)
    insertSql = ''
    values = []
    for i in messages:
        insertSql += '''INSERT INTO txns("txn_content", "block_number", "timestamp")
            VALUES(%s, %s, %s) RETURNING "txn_content";'''
        if not timestamp:
            values += [json.dumps(i), blockNumber, str(datetime.now())]
        else:
            values += [json.dumps(i), blockNumber, str(timestamp)]
    cur.execute(insertSql, values)
    conn.commit()
