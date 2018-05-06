import unittest
import os
import os.path
import shutil
import sys

def mock_ask_for_username():
	return "admin"

def mock_getpass():
	return "pass"

def mock_ask_for_peer_username():
	return "af"

def mock_peer_getpass():
	return "pass"

def mock_getPeers(self):
	return None

def mock_getAuth(self,json_message = None): 
	from login import ask_for_username
	from getpass import getpass
	from hashMe import hashMe
	import json

	ask_for_username = mock_ask_for_peer_username
	getpass = mock_getpass

	if json_message is not None:
		self.authenticated = json.loads(json_message['content'])
		print self.authenticated
	else:
		self.waitForAuth = True
		username = ask_for_username()
		hashed_password = hashMe(getpass())
		message = (username, hashed_password)
		self.authenticated = True
		return self.sendMessage(None, json.dumps(message), 5)
			

class UnitTests(unittest.TestCase):

	def test_create_Community_Peer_object(self):
		import login
		import getpass

		login.ask_for_username = mock_ask_for_username
		getpass.getpass = mock_getpass
		
		import community_peer

		mockcom = community_peer.Community_Peer(sim=True)
		mockcom.endPeer()

		self.assertIsInstance(mockcom, community_peer.Community_Peer)

	def test_create_Peer_object(self):
		from login import ask_for_username, find_hashed_password_by_user
		from getpass import getpass
		import json

		ask_for_username = mock_ask_for_username
		getpass = mock_getpass
		
		import peer

		peer.Peer.getAuth = mock_getAuth
		peer.Peer.getPeers = mock_getPeers

		mockpeer = peer.Peer('127.0.0.1',8000,True)
		mockpeer.endPeer()
		self.assertIsInstance(mockpeer, peer.Peer)

	def test_Peer_login(self):
		from login import ask_for_username, find_hashed_password_by_user
		from getpass import getpass
		import json

		ask_for_username = mock_ask_for_username
		getpass = mock_getpass
		
		import peer

		peer.Peer.getAuth = mock_getAuth
		peer.Peer.getPeers = mock_getPeers

		mockpeer = peer.Peer('127.0.0.1',8000,True)
		mockpeer.authenticated = False
		content = mockpeer.getAuth(json_message=None)

		recv_buffer_split = str(content).split('\0')
		content = recv_buffer_split[0]
		credentials = json.loads(json.loads(content)['content'])
		
		self.assertTrue(find_hashed_password_by_user(str(credentials[0]),str(credentials[1]), mockpeer.conn, mockpeer.cur))

		mockpeer.endPeer()
		
if __name__ == "__main__":
    unittest.main()