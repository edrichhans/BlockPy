import json
from hashMe import hashMe
from collections import OrderedDict, Sequence
from datetime import datetime

# For each block, we want to collect a set of transactions,
# create a header, hash it, and add it to the chain

def makeBlock(txns,chain):
    print txns

    parentBlock = chain[-1]
    parentHash  = parentBlock[u'blockHash']
    blockNumber = parentBlock[u'contents'][u'blockNumber'] + 1
    txnCount    = len(txns)
    blockTxn    = txns
    timestamp   = str(datetime.now())
    blockContents = {
        u'blockNumber':blockNumber,
        u'parentHash':parentHash,
        u'txnCount':txnCount,
        u'blockTxn':json.dumps(blockTxn),
        u'timestamp':timestamp
        }
    blockHash = hashMe(blockContents)
    block = {u'blockHash':blockHash,u'contents':blockContents}
    
    return block

def makeTxn(pubkey, recipient, content):
    txn = {u'_owner': pubkey, u'_recipient': recipient, u'_content': content}
    return txn