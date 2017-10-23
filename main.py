import time, json, socket
from sys import argv, exit
from block import makeBlock, makeTxn
from checking import checkChain, checkBlockValidity
from hashMe import hashMe
from chain import readChain, viewChain, writeChain

maxTxns = 1
blockLocation = 'JSON/sampleblock.json'

def main():
    s = socket.socket()
    s.bind(('localhost',9999))
    s.listen(5)

    print '\nReading contents of current chain...\n'
    chain = readChain(blockLocation)
    viewChain(chain)

    while True:
        c, address = s.accept()
        print 'Got connection from {0}'.format(address) + '\n'
        print 'Receiving...\n'
        l = c.recv(1024)
        txnList = []
        while (l):
            txn = json.loads(l)
            txn['content'] = hashMe(json.dumps(txn['content']))
            txnList.append(makeTxn(txn['_owner'], txn['_recipient'], txn['content']))
            if len(txnList) >= maxTxns:
                break
            print 'Receiving...\n'
            l = c.recv(1024)
        print 'Done Receiving\n'
        newBlock = makeBlock(txnList, chain)
        checkBlockValidity(newBlock, chain[-1])
        chain.append(newBlock)
        checkChain(chain)
        viewChain(chain)
        txnList = []
        print 'Writing to file...\n'
        writeChain(chain, blockLocation)
        c.send('Thank you for connecting')
        c.close()

if __name__ == '__main__':
    main()





