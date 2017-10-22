import json
import time
import math
from collections import OrderedDict
import hashlib

def jsonInput(finput):
	txnTable = []

	with open (finput) as f:
		data = json.load(f, object_pairs_hook=OrderedDict)

	for senders in data:
		senders['content'] = hashlib.sha256(json.dumps(senders['content'])).hexdigest()
		txnTable.append(createTxn(senders['_owner'], senders['_recipient'], senders['content']))
	
	return txnTable
	

def jsonOutput(txnTable, foutput):

	with open(foutput,"w") as foutput:
		json.dump(txnTable, foutput, indent=4)


def createTxn(pubkey, recipient, content):

	txn = OrderedDict()
	txn['_owner'] = pubkey
	txn['_recipient'] = recipient
	txn['content'] = content

	return txn

#jsonOutput(jsonInput("inputJSON.json"), "sampleoutput.json")

# with open("inputJSON.json", "r") as i:
# 	jsonString = i.read()

# print jsonString

'''notes
get prev hash
get current hash (hash everything)
since nonce is time based, what if different time zones manipulated by rogue user? 
how about letting verifiers check if nonce is closely accurateto UTC?
concept of attaching blockchains with this kind of nonce
'''