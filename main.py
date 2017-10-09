import json, copy

from hashMe import hashMe
from sample import makeTransaction
from create_block import updateState, isValidTxn, makeBlock
from checking import checkBlockHash, checkBlockValidity, checkChain

# Now let's create a large set of transactions, then chunk them into blocks.

txnBuffer = [makeTransaction() for i in range(30)]

# Because the genesis block isn't linked to any prior block,
# it gets treated a bit differently, and we can arbitrarily set
# the system state. In our case, we'll create accounts for
# our two users (Alice and Bob) and give them 50 coins each.

state = {u'Alice':50, u'Bob':50}  # Define the initial state
genesisBlockTxns = [state]
genesisBlockContents = {u'blockNumber':0,u'parentHash':None,u'txnCount':1,u'txns':genesisBlockTxns}
genesisHash = hashMe( genesisBlockContents )
genesisBlock = {u'hash':genesisHash,u'contents':genesisBlockContents}
genesisBlockStr = json.dumps(genesisBlock, sort_keys=True)

# This becomes the first element from which everything else will be linked.

chain = [genesisBlock]

# Let's use this to process our transaction buffer into a set of blocks:

blockSizeLimit = 5  # Arbitrary number of transactions per block- 
               #  this is chosen by the block miner, and can vary between blocks!

while len(txnBuffer) > 0:
    bufferStartSize = len(txnBuffer)
    
    ## Gather a set of valid transactions for inclusion
    txnList = []
    while (len(txnBuffer) > 0) & (len(txnList) < blockSizeLimit):
        newTxn = txnBuffer.pop()
        validTxn = isValidTxn(newTxn,state) # This will return False if txn is invalid
        
        if validTxn:           # If we got a valid state, not 'False'
            txnList.append(newTxn)
            state = updateState(newTxn,state)
        else:
            print("ignored transaction")
            sys.stdout.flush()
            continue  # This was an invalid transaction; ignore it and move on
        
    ## Make a block
    myBlock = makeBlock(txnList,chain)
    chain.append(myBlock)

# viewing the chain and the current state

print chain[0]
print chain[1]
print state

# We can now check the validity of the state:

checkChain(chain)

# And even if we are loading the chain from a text file,
# e.g. from backup or loading it for the first time,
# we can check the integrity of the chain and create the current state:

chainAsText = json.dumps(chain,sort_keys=True)
checkChain(chainAsText)

# We've seen how to verify a copy of the blockchain,
# and how to bundle transactions into a block.
# If we recieve a block from somewhere else,
# verifying it and adding it to our blockchain is easy.

# Let's say that the following code runs on Node A, which mines the block:

nodeBchain = copy.copy(chain)
nodeBtxns  = [makeTransaction() for i in range(5)]
newBlock   = makeBlock(nodeBtxns,nodeBchain)

# Now assume that the newBlock is transmitted to our node,
# and we want to check it and update our state if it is a valid block:

print("Blockchain on Node A is currently %s blocks long"%len(chain))

try:
    print("New Block Received; checking validity...")
    state = checkBlockValidity(newBlock,chain[-1],state) # Update the state- this will throw an error if the block is invalid!
    chain.append(newBlock)
except:
    print("Invalid block; ignoring and waiting for the next block...")

print("Blockchain on Node A is now %s blocks long"%len(chain))