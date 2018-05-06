import unittest
import os
import os.path
import shutil
import sys

#change this
def mock_ask_for_username():
	return "admin"

#change this
def mock_getpass():
	return "pass"

#change this
def mock_getpeername():
	return ('127.0.0.1',8000)

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

def mock_addNewPeer(self, peername, json_message):
	from nacl.encoding import HexEncoder
	from nacl.signing import SigningKey, VerifyKey
	import json

	peer_info = json.loads(json_message)['content']
	sender_public_key = VerifyKey(HexEncoder.decode(peer_info[2]))
	self.public_key_list[str(peer_info[0]), peer_info[1]] = sender_public_key
	self.port_equiv[peername] = (peer_info[0], peer_info[1])
	encodedPubKeys = {}

	for addr in self.public_key_list:
		encodedPubKeys[str(addr)] = self.public_key_list[addr].encode(encoder=HexEncoder)
	
	return encodedPubKeys

def mock_sendMinerList(self):
	if len(self.public_key_list) < 3:
		for addr in self.public_key_list:
			if addr != (self.ip_addr, self.port):
				del self.miners[:]
				self.miners.append(addr)

	if self.miners:
		return self.miners

class UnitTests(unittest.TestCase):
		
	def test_Community_Peer_addNewPeer(self):
		import login
		import getpass
		import json
		from nacl.encoding import HexEncoder

		import peer

		peer.Peer.getAuth = mock_getAuth
		peer.Peer.getPeers = mock_getPeers

		#change this
		mockpeer = peer.Peer('127.0.0.1',8000,True)

		mockip = mockpeer.ip_addr
		mockport = mockpeer.port
		mockpubkey = mockpeer.pubkey
		message = mockpeer.getPeers()[mockpeer.community_ip]
		json_message = message.split('\0')[0]

		mockpeer.endPeer()

		#---------------------------------------------
		login.ask_for_username = mock_ask_for_username
		getpass.getpass = mock_getpass
		
		import community_peer

		mockcom = community_peer.Community_Peer(sim=True)

		community_peer.Community_Peer.addNewPeer = mock_addNewPeer
		pubkeys = mockcom.addNewPeer((mockip,mockport),json_message)

		self.assertEqual(pubkeys[str((mockcom.ip_addr,mockcom.port))],mockcom.pubkey.encode(HexEncoder))
		self.assertEqual(pubkeys[str((mockip,mockport))],mockpubkey.encode(HexEncoder))

		community_peer.Community_Peer.addNewPeer = mock_sendMinerList
		miners = mockcom.addNewPeer()

		self.assertEqual(miners[0],(mockip,mockport))

		mockcom.endPeer()

	def test_Peer_getPeers(self):
		import json
		import peer
		from nacl.encoding import HexEncoder

		peer.Peer.getAuth = mock_getAuth
		peer.Peer.getPeers = mock_getPeers

		#change this
		mockpeer = peer.Peer('127.0.0.1',8000,True)

		message = mockpeer.getPeers()[mockpeer.community_ip]

		#change this
		correctpacket = {"_category":"4",
			"content":[mockpeer.ip_addr,mockpeer.port,mockpeer.pubkey.encode(HexEncoder)],
			"_owner": mockpeer.pubkey.encode(HexEncoder),
			"_recipient": None
			}

		message = json.loads(message.split('\0')[0])
		self.assertEqual(message["_category"],"4")
		self.assertEqual(message["content"],[mockpeer.ip_addr,mockpeer.port,mockpeer.pubkey.encode(HexEncoder)])
		self.assertEqual(message["_owner"],mockpeer.pubkey.encode(HexEncoder))
		self.assertEqual(message["_recipient"],None)

		#change this
		peer_addr=[('127.0.0.1','1'),('127.0.0.1','2'),('127.0.0.1','3'),('127.0.0.1','4')]
		
		message = mockpeer.getPeers(peer_addr,False)

		#change this
		correctpacket = {"_category":"7",
			"content":[mockpeer.ip_addr,mockpeer.port,mockpeer.pubkey.encode(HexEncoder)],
			"_owner": mockpeer.pubkey.encode(HexEncoder),
			"_recipient": None
			}

		for i in peer_addr:
			mockmessage = json.loads(message[i].split('\0')[0])
			self.assertEqual(mockmessage["_category"],correctpacket["_category"])
			self.assertEqual(mockmessage["content"],correctpacket['content'])
			self.assertEqual(mockmessage["_owner"],correctpacket['_owner'])
			self.assertEqual(mockmessage["_recipient"],correctpacket['_recipient'])

		mockpeer.endPeer()

if __name__ == "__main__":
    unittest.main()