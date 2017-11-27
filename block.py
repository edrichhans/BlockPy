from hashMe import hashMe
from collections import OrderedDict, Sequence
from datetime import date

# For each block, we want to collect a set of transactions,
# create a header, hash it, and add it to the chain

def makeBlock(txns,chain):

    if not isinstance(txns, Sequence) and isinstance(txns, basestring):
        txns = [str(txns)]

    parentBlock = chain[-1]
    parentHash  = parentBlock[u'blockHash']
    blockNumber = parentBlock[u'contents'][u'blockNumber'] + 1
    txnCount    = len(txns)
    blockTxn    = hashMe(txns)
    timestamp   = str(date.today())
    blockContents = {
        u'blockNumber':blockNumber,
        u'parentHash':parentHash,
        u'txnCount':txnCount,
        u'blockTxn':blockTxn,
        u'timestamp':timestamp
        }
    blockHash = hashMe( blockContents )
    block = {u'blockHash':blockHash,u'contents':blockContents}
    
    return block

def makeTxn(pubkey, recipient, content):
    txn = OrderedDict()
    txn['_owner'] = pubkey
    txn['_recipient'] = recipient
    txn['content'] = content

    return txn