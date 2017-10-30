import json
import time
import math
from collections import OrderedDict
import hashlib

def makeBlock(finput,chain):

	with open (finput) as f:
		data = json.load(f, object_pairs_hook=OrderedDict)

	for senders in data:
		txns = hashlib.sha256(json.dumps(senders)).hexdigest()
		parentBlock = chain[-1]
		parentHash  = parentBlock['hash']
		blockNumber = parentBlock['contents']['blockNumber'] + 1
		blockContents = {'blockNumber':blockNumber,'parentHash':parentHash,
						'txnCount':len(txns),'txns':txns}
		blockHash = hashlib.sha256(blockContents).hexdigest()
		block = {'hash':blockHash,'contents':blockContents}
		chain.append(block)
    return chain


def blkJSONOutput(chain, foutput):

	with open(foutput,"w") as foutput:
		json.dump(chain, foutput, indent=4)

genesisBlockContents = {
	'blockNumber':0,
	'parentHash':None,
	'blockTxn':None
}
genesisHash = hashlib.sha256(genesisBlockContents).hexdigest()
genesisBlock = {
	'hash':genesisHash,
	'contents':genesisBlockContents
}
chain = [genesisBlock]
blkJSONOutput(makeBlock("sampleoutput.json",chain), "blkListOutput.json")

