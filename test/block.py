import json
from hashMe import hashMe
from collections import OrderedDict, Sequence
from datetime import datetime
from blockpy_logging import logger

# For each block, we want to collect a set of transactions,
# create a header, hash it, and add it to the chain

def makeBlock(txns,chain):
    merkleRoot = createMerkle(txns)

    parentBlock = chain[-1]
    parentHash  = parentBlock[u'blockHash']
    blockNumber = parentBlock[u'contents'][u'blockNumber'] + 1
    txnCount    = len(txns)
    blockTxn    = merkleRoot
    timestamp   = str(datetime.now())
    blockContents = {
        u'blockNumber':blockNumber,
        u'parentHash':parentHash,
        u'txnCount':txnCount,
        u'blockTxn':merkleRoot,
        u'timestamp':timestamp
        }
    blockHash = hashMe(blockContents)
    block = {u'blockHash':blockHash,u'contents':blockContents}

    logger.info('Created Block:',
            extra={'block': block})
    
    return block

def makeTxn(pubkey, recipient, content):
    txn = {u'_owner': pubkey, u'_recipient': recipient, u'_content': content}
    return txn

def createMerkle(txns):
    if(len(txns)) <= 1:
        return txns[0]
    nextLevel = []
    for i in xrange(0, len(txns), 2):
        if i+1 >= len(txns):
            nextLevel.append(hashMe(txns[i]))
        else:
            nextLevel.append(hashMe(hashMe(txns[i])+hashMe(txns[i+1])))
    return createMerkle(nextLevel)
