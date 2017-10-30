import json
from collections import OrderedDict
from hashMe import hashMe

def makeBlock(finput,chain):

	with open (finput, "w") as f:
		data = json.load(f, object_pairs_hook=OrderedDict)

	for senders in data:
		txns = hashMe(json.dumps(senders))
		parentBlock = chain[-1]
		parentHash  = parentBlock['hash']
		blockNumber = parentBlock['contents']['blockNumber'] + 1
		blockContents = {u'parentHash':parentHash,u'blockNumber':blockNumber,u'blockTxn':txns}
		blockHash = hashMe( blockContents )
		block = {'hash':blockHash,'contents':blockContents}
		chain.append(block)
	return chain
