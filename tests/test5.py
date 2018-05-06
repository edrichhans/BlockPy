import unittest
import os
import os.path
import shutil
import sys

def mock_addToChain(newBlock, conn, cur):
	return 2

def mock_addToTxns(txn, conn, cur, blockNumber):
	return None

#change this
def mock_ask_for_username():
	return "admin"

#change this
def mock_getpass():
	return "pass"

#change this
def mock_peer_ask_for_username():
	return "af"

#change this
def mock_peer_getpass():
	return "pass"

def mock_waitForSignedBlock(self, peer, json_message, newblock):
	from hashMe import hashMe
	import json
	from nacl.encoding import HexEncoder
	from main import create, addToChain, addToTxns
	from chain import readChainSql, readTxnsSql
	from nacl.signing import SigningKey, VerifyKey

	self.newBlock, self.txnList = create(newblock, self.conn, self.cur)

	if peer in self.port_equiv:
		peer = self.port_equiv[peer]

	if peer in self.received_transaction_from:
		verifier = VerifyKey(HexEncoder.decode(self.received_transaction_from[peer]))
		
		if verifier.verify(json_message['content'][0].decode('base64')):
			raw_pubkey = verifier.encode(HexEncoder)
			p = ''.join([str(ord(c)) for c in raw_pubkey])
			nonce = json_message['content'][1]
			self.potential_miners[peer] = abs(int(hashMe(self.newBlock['blockHash']+nonce), 36) - int(p[:100]))
			del self.received_transaction_from[peer]
		else:
			return False
	else:
		return False

	if len(self.received_transaction_from) == 0:
		blockNumber = addToChain(self.newBlock, self.conn, self.cur)
		addToTxns(self.txnList, self.conn, self.cur, blockNumber)
		self.received_transaction_from = {}
		self.pendingBlocks = []

		chain = readChainSql(self.conn, self.cur)
		txns = readTxnsSql(self.conn, self.cur)
		
		self.miners = [i[0] for i in sorted(self.potential_miners.iteritems(), key=lambda (k,v): (v,k))][:(int)(len(self.potential_miners)/3)+1]
		for i, self.miner in enumerate(self.miners):
			if self.miner in self.port_equiv:
				self.miners[i] = self.port_equiv[self.miner]
		self.potential_miners = {}
		return self.miners

def mock_collectBlocks(self, json_message):
	import json
	from collections import Counter

	content = json.loads(json_message['content'])
	try:
		self.pendingBlocks.append((content['block']['blockHash'],content))
		if len(self.pendingBlocks) == len(self.miners):
			content = Counter([x[0] for x in self.pendingBlocks])
			for i in self.pendingBlocks:
				if i[0] == content.most_common(1)[0][0]:
					content = i[1]
					break
			return self.returnToVerify(content)
	except Exception as e:
		print e

def mock_returnToVerify(self, content):
	import json

	messages = []
	self.newBlock = content['block']
	self.txnList = eval(content['txnList'])
	self.received_transaction_from = eval(content['contributing'])
	for peer in self.received_transaction_from:
		if peer in self.port_equiv.values():
			for key,value in self.port_equiv.items():
				if peer == value:
					messages.append(json.dumps(self.newBlock))
		else:
			messages.append(json.dumps(self.newBlock))

	return messages

def mock_authenticate(self, json_message):
	from login import find_hashed_password_by_user
	import json 

	credentials = json.loads(json_message['content'])
	if find_hashed_password_by_user(str(credentials[0]),str(credentials[1]), self.conn, self.cur):
		return True
	else:
		return False
		
class UnitTests(unittest.TestCase):

	def test_Community_Peer_waitForSignedBlock(self):
		from uuid import uuid1
		from hashMe import hashMe
		import login, getpass, json
		from nacl.encoding import HexEncoder
		from nacl.signing import SigningKey, VerifyKey

		login.ask_for_username = mock_ask_for_username
		getpass.getpass = mock_getpass
		
		import community_peer

		community_peer.Community_Peer.waitForSignedBlock = mock_waitForSignedBlock
		mockcom = community_peer.Community_Peer(sim=True)

		#change this
		newBlock = [
			json.dumps({'_owner':mockcom.pubkey.encode(HexEncoder), '_recipient':'dummy recipient', 'content': "dummy content"}),
			json.dumps({'_owner':mockcom.pubkey.encode(HexEncoder), '_recipient':'dummy recipient', 'content': "dummy content"}),
			json.dumps({'_owner':mockcom.pubkey.encode(HexEncoder), '_recipient':'dummy recipient', 'content': "dummy content"}),
			json.dumps({'_owner':mockcom.pubkey.encode(HexEncoder), '_recipient':'dummy recipient', 'content': "dummy content"})
		]

		#change this
		mockcom.received_transaction_from[('127.0.0.1',1)] = mockcom.pubkey.encode(HexEncoder)
		message = mockcom.privkey.sign(str(hashMe("dummy message"))).encode('base64')
		peer = ('127.0.0.1',1)

		json_message={}
		json_message['content'] = [None, None]
		json_message['content'][0] = message
		json_message['content'][1] = hashMe(uuid1().hex)

		self.assertEqual(mockcom.waitForSignedBlock(peer, json_message, newBlock),[peer])

		mockcom.endPeer()

	def test_Community_Peer_returntoVerify(self):
		from hashMe import hashMe
		import login, getpass, json
		from nacl.encoding import HexEncoder

		login.ask_for_username = mock_ask_for_username
		getpass.getpass = mock_getpass
		
		import community_peer

		community_peer.Community_Peer.collectBlocks = mock_collectBlocks
		community_peer.Community_Peer.returnToVerify = mock_returnToVerify
		mockcom = community_peer.Community_Peer(sim=True)

		#change this
		mockcom.miners = {('127.0.0.1',1),('127.0.0.1',2),('127.0.0.1',3)}
		mockcom.port_equiv = {
			('127.0.0.1',4): ('127.0.0.1',14), 
			('127.0.0.1',5): ('127.0.0.1',15),
			('127.0.0.1',16): ('127.0.0.1',6)
		}

		#change this
		json_message = {}
		json_message['content'] =  json.dumps({'block': {'blockHash': "dummy hash", 'content': "dummy content"},
									'txnList': "[]",
									'contributing': "[('127.0.0.1',4), ('127.0.0.1',5), ('127.0.0.1',6)]"
									})
		mockcom.collectBlocks(json_message)
		json_message['content'] =  json.dumps({'block': {'blockHash': "dummy hash", 'content': "dummy content"},
									'txnList': "[]",
									'contributing': "[('127.0.0.1',4), ('127.0.0.1',5), ('127.0.0.1',6)]"
									})
		mockcom.collectBlocks(json_message)
		json_message['content'] =  json.dumps({'block': {'blockHash': "dummy hash 2", 'content': "dummy content 2"},
									'txnList': "[]",
									'contributing': "[('127.0.0.1',4), ('127.0.0.1',5), ('127.0.0.1',7)]"
									})
		block = mockcom.collectBlocks(json_message)

		self.assertEqual(len(block), len(mockcom.miners))
		self.assertEqual(json.loads(block[0])['content'], "dummy content")
		self.assertEqual(json.loads(block[0])['blockHash'], "dummy hash")

		mockcom.endPeer()

	def test_Community_Peer_authenticate(self):
		from hashMe import hashMe
		import login, getpass, json
		from nacl.encoding import HexEncoder

		login.ask_for_username = mock_ask_for_username
		getpass.getpass = mock_getpass
		
		import community_peer

		community_peer.Community_Peer.authenticate = mock_authenticate
		mockcom = community_peer.Community_Peer(sim=True)

		json_message = {'content': json.dumps([mock_peer_ask_for_username(),hashMe(mock_peer_getpass())])}
		self.assertTrue(mockcom.authenticate(json_message))

		mockcom.endPeer()

if __name__ == "__main__":
    unittest.main()