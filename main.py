import time, json, py2p
from sys import argv, exit
from block import makeBlock, makeTxn
from checking import checkChain, checkBlockValidity
from hashMe import hashMe
from chain import readChain, viewChain, writeChain

# Create Mesh Socket at port 4444
sock = py2p.MeshSocket('0.0.0.0', 4444)
maxTxns = 1
blockLocation = 'JSON/Chain.json'

def main():
    print '\nReading contents of current chain...\n'
    chain = readChain(blockLocation)
    viewChain(chain)

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
            checkBlockValidity(newBlock, chain[-1])
            chain.append(newBlock)
            checkChain(chain)
            viewChain(chain)
            print 'Writing to file...\n'
            writeChain(chain, blockLocation)

if __name__ == '__main__':
    main()





