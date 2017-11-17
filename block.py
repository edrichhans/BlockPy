from hashMe import hashMe
from collections import OrderedDict, Sequence
from datetime import time

# For each block, we want to collect a set of transactions,
# create a header, hash it, and add it to the chain

def makeBlock(txns,chain):

    if not isinstance(txns, Sequence) and isinstance(txns, basestring):
        txns = [str(txns)]

    parentBlock = chain[-1]
    parentHash  = parentBlock[u'hash']
    blockNumber = parentBlock[u'contents'][u'blockNumber'] + 1
    txnCount    = len(txns)
    blockContents = {
        u'blockNumber':blockNumber,
        u'parentHash':parentHash,
        u'txnCount':txnCount,
        u'blockTxn':hashMe(txns),
        u'timestamp':str(date.today())
        }
    blockHash = hashMe( blockContents )
    block = {u'hash':blockHash,u'contents':blockContents}
    
    return block

def makeTxn(pubkey, recipient, content):
    txn = OrderedDict()
    txn['_owner'] = pubkey
    txn['_recipient'] = recipient
    txn['content'] = content

    return txn