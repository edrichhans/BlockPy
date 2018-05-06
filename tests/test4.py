import unittest
import os
import os.path
import shutil
import sys

def mock_None(self):
	return None

def mock_getAuth(self): 
	self.waitForAuth = True
	self.authenticated = True

def mock_getPeers(self, peer_addr = [], connect_to_community_peer = True):
	from nacl.encoding import HexEncoder
	import json 

	result = {}

	if connect_to_community_peer:
		try:
			if(self.authenticated == False):
				None
			else:
				message = (self.ip_addr,self.port,self.pubkey.encode(encoder=HexEncoder))
				result[self.community_ip] = self.sendMessage(None, message, 4)
		except Exception as e:
			print 'Community Server Error: ', e
	else:
		for addr in peer_addr:
			message = (self.ip_addr,self.port,self.pubkey.encode(encoder=HexEncoder))
			result[addr] = self.sendMessage(None,message,7)
	
	return result

def mock_sendToMiners(self, recpubkey=None, message=None):
	import json

	messages = {}
	raw_string = self.sendMessage(recpubkey,message,1)
	for miner in self.miners:
		if miner in self.port_equiv.values():
			for key,value in self.port_equiv.items():
				if miner == value:
					messages[key] = raw_string
		else:
			messages[miner] = raw_string
	
	if self.is_miner:
		raw_string = self.sendMessage(recpubkey,message,1)[:-1]
		json_message = json.loads(raw_string)
		category = str(json_message['_category'])
		if category == str(1):
			messages[(self.ip_addr,self.port)] = raw_string

	return messages

def mock_waitForTxn(self, json_message, message, socket = None):
	from main import create
	import json

	try:
		owner = json_message['_owner']
		if socket is None and self.is_miner:
			self.received_transaction_from[(self.ip_addr, self.port)] = owner
			self.received_transaction_from_reverse[(self.ip_addr, self.port)] = owner
		else:
			if socket in self.port_equiv:
				self.received_transaction_from[socket] = owner
				self.received_transaction_from_reverse[self.port_equiv[socket]] = owner
			elif socket in self.port_equiv.values():
				for key,value in self.port_equiv.items():
					if socket == value:
						self.received_transaction_from_reverse[value] = owner
						self.received_transaction_from[key] = owner
			else:
				print 'self.port_equiv not set properly.'

		self.messages.append(message)
		if len(self.messages) >= self.max_txns:
			self.newBlock, self.txnList = create(self.messages, self.conn, self.cur)
			packet = {'block': self.newBlock, 'txnList': str(self.txnList), 'contributing': str(self.received_transaction_from_reverse)}
			return self.sendMessage(None,json.dumps(packet), 9)
		return self.messages
	except Exception as e:
		print "SEND ERROR: ", e
		return None

def mock_verifyBlock(self, peer, message):
	from hashMe import hashMe
	import json
	from uuid import uuid1

	# generate nonce
	nonce = hashMe(uuid1().hex)
	# get block
	block = json.loads(json.loads(message)['content'])
	# generate signature
	signature = self.privkey.sign(str(hashMe(json.dumps(block))))
	# send message
	return {peer: [signature.encode('base64'), nonce, 3]}
	
def json_serial( obj):
	import datetime
	if isinstance(obj, (datetime.datetime, datetime.date)):
		return obj.isoformat()
	raise TypeError("Type %s is not serializable" % type(obj))

class UnitTests(unittest.TestCase):

	def test_Peer_sendMessage(self):
		import json
		import peer
		from hashMe import hashMe
		from nacl.encoding import HexEncoder

		peer.Peer.getAuth = mock_getAuth
		peer.Peer.getPeers = mock_None

		#change this
		mockpeer = peer.Peer('127.0.0.1',8000,True)

		#change this
		content = "Hi"
		recpubkey = "dummy"
		correctpacket = {
			'_owner': mockpeer.pubkey.encode(HexEncoder),
			'_recipient': recpubkey,
			'_category': "1",
			'content': mockpeer.privkey.sign(str(hashMe(content))).encode('base64')}

		block = mockpeer.sendMessage(recpubkey, content, 1)
		message = block.split('\0')[0]

		self.assertEqual(json.loads(message)['_category'],correctpacket['_category'])
		self.assertEqual(json.loads(message)['_owner'],correctpacket['_owner'])
		self.assertEqual(json.loads(message)['_recipient'],correctpacket['_recipient'])
		self.assertEqual(json.loads(message)['content'],correctpacket['content'])

		mockpeer.endPeer()

	def test_Peer_sendToMiners(self):
		import json
		import peer
		from hashMe import hashMe
		from nacl.encoding import HexEncoder

		peer.Peer.getAuth = mock_getAuth
		peer.Peer.getPeers = mock_None
		peer.Peer.sendToMiners = mock_sendToMiners

		#change this
		mockpeer = peer.Peer('127.0.0.1',8000,True)
		mockpeer.miners = [('127.0.0.1',1),('127.0.0.1',2),('127.0.0.1',3),('127.0.0.1',4)]
		mockpeer.port_equiv = {
				('127.0.0.1',11):('127.0.0.1',1),
				('127.0.0.1',12):('127.0.0.1',2),
				('127.0.0.1',3):('127.0.0.1',13),
				('127.0.0.1',4):('127.0.0.1',14)
			}

		mockpeer.is_miner = True

		#change this
		sentmessages = mockpeer.sendToMiners(recpubkey="samplepubkey",message="sample message")
		
		self.assertEqual(len(sentmessages),5)

		#change this
		for address in sentmessages:
			self.assertIn(address,[
					(mockpeer.ip_addr,mockpeer.port),
					('127.0.0.1',11),
					('127.0.0.1',12),
					('127.0.0.1',3),
					('127.0.0.1',4)
				])

		mockpeer.endPeer()

	def test_Peer_waitForTxn(self):
		import json
		import peer
		from hashMe import hashMe
		from nacl.encoding import HexEncoder

		peer.Peer.getAuth = mock_getAuth
		peer.Peer.getPeers = mock_None
		peer.Peer.waitForTxn = mock_waitForTxn

		#change this
		mockpeer = peer.Peer('127.0.0.1',8000,True)
		mockpeer.max_txns = 3

		mockpeer.is_miner = True

		#change this
		message = {
				"_owner": mockpeer.pubkey.encode(HexEncoder),
				"_recipient": "dummy",
				"_category": "1",
				"content": "dummy message"
			}

		json_message = json.dumps(message)

		#change this
		mockpeer.port_equiv = {('127.0.0.1',1): ('127.0.0.1',11), ('127.0.0.1',12): ('127.0.0.1',2)}
		
		mockpeer.waitForTxn(json.loads(json_message),json_message,None)
		self.assertEqual(len(mockpeer.messages),1)
		self.assertEqual(mockpeer.received_transaction_from[(mockpeer.ip_addr, mockpeer.port)], message["_owner"])
		self.assertEqual(mockpeer.received_transaction_from_reverse[(mockpeer.ip_addr, mockpeer.port)], message["_owner"])
		
		#change this
		socket = ("127.0.0.1",1)

		mockpeer.waitForTxn(json.loads(json_message),json_message,socket)
		self.assertEqual(len(mockpeer.messages),2)
		self.assertEqual(mockpeer.received_transaction_from[socket], message["_owner"])
		self.assertEqual(mockpeer.received_transaction_from_reverse[mockpeer.port_equiv[socket]], message["_owner"])
		
		#change this
		socket = ("127.0.0.1",2)

		newmessage = mockpeer.waitForTxn(json.loads(json_message),json_message,socket)
		newmessage = newmessage.split('\0')
		json_message = json.loads(newmessage[0])
		content = json.loads(json_message['content'])

		#change this
		self.assertEqual(len(mockpeer.messages),len(mockpeer.port_equiv)+1)
		self.assertEqual(len(eval(content['contributing'])),len(mockpeer.port_equiv)+1)
		self.assertEqual(len(eval(content['txnList'])),len(mockpeer.port_equiv)+1)
		self.assertEqual(content['block']['contents']['txnCount'],len(mockpeer.port_equiv)+1)

		#change this
		reversesocket = ("127.0.0.1",12)

		self.assertEqual(mockpeer.received_transaction_from[reversesocket], message["_owner"])
		self.assertEqual(mockpeer.received_transaction_from_reverse[socket], message["_owner"])
	
		mockpeer.endPeer()		

	def test_Peer_verifyBlock(self):
		import json
		import peer
		from hashMe import hashMe
		from nacl.encoding import HexEncoder
		from uuid import uuid1

		peer.Peer.getAuth = mock_getAuth
		peer.Peer.getPeers = mock_None
		peer.Peer.verifyBlock = mock_verifyBlock

		#change this
		mockpeer = peer.Peer('127.0.0.1',8000,True)
		socket = ('127.0.0.1',1)
		packet = {
			'content':json.dumps("dummy message")
		}

		block = mockpeer.verifyBlock(socket,json.dumps(packet))

		self.assertEqual(block[socket][0], mockpeer.privkey.sign(str(hashMe(json.loads(packet['content'])))).encode('base64'))
		self.assertIsNotNone(block[socket][1])
		self.assertEqual(block[socket][2], 3)

		mockpeer.endPeer()

	def test_Peer_updateTables(self):
		import json
		import peer
		from chain import readChainSql, readTxnsSql
		import datetime

		peer.Peer.getAuth = mock_getAuth
		peer.Peer.getPeers = mock_None

		#change this
		mockpeer = peer.Peer('127.0.0.1',8000,True)
		
		chain = readChainSql(mockpeer.conn, mockpeer.cur)
		txns = readTxnsSql(mockpeer.conn, mockpeer.cur)
		json_message = mockpeer.sendMessage(None,json.dumps({'chain': chain, 'txns': txns}, default=json_serial), 10)
		json_message =json_message.split('\0')[0]
		json_message = json.loads(json_message)

		self.assertIsNone(mockpeer.updateTables(json_message))
		mockpeer.endPeer()

	def test_Peer_verifyTxn(self):
		import json
		import peer

		peer.Peer.getAuth = mock_getAuth
		peer.Peer.getPeers = mock_None

		#change this
		mockpeer = peer.Peer('127.0.0.1',8000,True)

		self.assertTrue(mockpeer.getTxn(1)[1])
		self.assertFalse(mockpeer.getTxn(-1)[-1])

		mockpeer.endPeer()

if __name__ == "__main__":
    unittest.main()