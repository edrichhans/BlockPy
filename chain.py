import json, psycopg2
from datetime import date
from collections import OrderedDict
from hashMe import hashMe

def readChain(finput):
    chain = []
    try:
        with open (finput, 'r') as f:
            chainJSON = json.load(f, object_pairs_hook=OrderedDict)
        for blockJSON in chainJSON:
            parentHash = blockJSON['contents']['parentHash']
            blockTxn = blockJSON['contents']['blockTxn']
            txnCount = blockJSON['contents']['txnCount']
            blockNumber = blockJSON['contents']['blockNumber']
            timestamp = blockJSON['contents']['timestamp']
            block = {
                'hash': blockJSON['hash'], 
                'contents': {
                    'parentHash': parentHash, 
                    'txnCount': txnCount,
                    'blockTxn': blockTxn, 
                    'blockNumber': blockNumber,
                    'timestamp': timestamp
                    #'digital signature': 
                    }
                }
            chain.append(block)

        return chain
    except IOError:

        print "No chain found\n"
        with open(finput, 'w') as f:
            genesisBlockContents = {
                'blockNumber':0,
                'parentHash':None,
                'txnCount':0,
                'blockTxn':None,
                'timestamp': str(date.today())
            }
            genesisHash = hashMe(genesisBlockContents)
            genesisBlock = {
                'hash':genesisHash,
                'contents':genesisBlockContents
            }
            chain = [genesisBlock]
            json.dump(chain, f)
            return chain

def readChainSql(cur):
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

def viewChain(chain):
    for block in chain:
        blockHash = block['hash']
        hashLen = len(blockHash)
        blockTxn = block['contents']['blockTxn']
        blockNumberFormatted = '| BlockNumber: ' + str(block['contents']['blockNumber'])
        print ('=' * (hashLen+4))
        print blockNumberFormatted + ' ' * (hashLen - len(blockNumberFormatted) + 2) + ' |'
        print ('=' * (hashLen+4))
        print '|' + ' ' * ((hashLen/2)-1) + 'hash' + ' ' * ((hashLen/2)-1) + '|'
        print '| ' + block['hash'] + ' |'
        print '|' + ' ' * (hashLen+2) + '|'
        print '|' + ' ' * ((hashLen/2)-3) + 'blockTxn' + ' ' * ((hashLen/2)-3) + '|'
        print '| ' + (blockTxn if blockTxn != None else ' ' * ((hashLen/2)-2) + 'NULL' + ' ' * ((hashLen/2)-2)) + ' |'
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

def writeChain(chain, foutput):
    with open(foutput,'w') as foutput:
        json.dump(chain, foutput, indent=4)