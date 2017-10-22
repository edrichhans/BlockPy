import time, json, socket, hashlib
from sys import argv, exit
from collections import OrderedDict
from json_filemaker import jsonOutput, createTxn
from json_createblock import blkJSONOutput
from create_block import makeBlock
from checking import checkChain, checkBlockValidity

def readChain(finput):
    with open (finput) as f:
        chainJSON = json.load(f, object_pairs_hook=OrderedDict)

    chain = []

    for blockJSON in chainJSON:
        parentHash = blockJSON['contents']['parentHash']
        blockTxn = blockJSON['contents']['blockTxn']
        blockNumber = blockJSON['contents']['blockNumber']
        block = {'hash': blockJSON['hash'], 'contents': {'parentHash': parentHash, 'blockTxn': blockTxn, 'blockNumber': blockNumber}}
        chain.append(block)

    return chain

def viewChain(chain):
    for i in chain:
        print i

if __name__ == '__main__':
    s = socket.socket()
    s.bind(("localhost",9999))
    s.listen(5)
    print "Reading contents of current block..."
    chain = readChain('./JSON/sampleblock.json')
    viewChain(chain)

    while True:
        c, address = s.accept()
        print 'Got connection from', address
        print "Receiving..."
        l = c.recv(1024)
        txnList = []
        while (l):
            print l
            txn = json.loads(l)
            txn['content'] = hashlib.sha256(json.dumps(txn['content'])).hexdigest()
            txnList.append(createTxn(txn['_owner'], txn['_recipient'], txn['content']))
            if len(txnList) >= 5:
                break
            print "Receiving..."
            l = c.recv(1024)
        print "Done Receiving"
        newBlock = makeBlock(txnList, chain)
        checkBlockValidity(newBlock, chain[-1])
        chain.append(newBlock)
        checkChain(chain)
        viewChain(chain)
        txnList = []
        print "Writing to file..."
        blkJSONOutput(chain, "JSON/sampleblock.json")
        c.send('Thank you for connecting')
        c.close()






