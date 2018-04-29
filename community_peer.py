
'''

Change ip address and port of commmunity peer before running

'''

import json, socket, sys, getopt, select, datetime, time
from threading import Thread
from main import create, addToChain, connect, disconnect, addToTxns
from chain import readChainSql, readTxnsSql
from hashMe import hashMe
from nacl.encoding import HexEncoder
from nacl.signing import SigningKey, VerifyKey
from nacl.hash import sha256
from Crypto import Random
from uuid import uuid1
from blockpy_logging import logger
<<<<<<< Updated upstream
from Queue import *
import pickle
from login import find_hashed_password_by_user, ask_for_username, ask_for_password, checkIfUsersExist, store_info, checkIfAdminExist
=======
from collections import Counter
from login import find_hashed_password_by_user, ask_for_username, ask_for_password, checkIfUsersExist, store_info, checkIfAdminExist, dropUsers
>>>>>>> Stashed changes
import getpass


class Community_Peer(Thread):

	def __init__(self,ip_address = '127.0.0.1', port = 5000):
		self.privkey = SigningKey.generate()
		self.pubkey = self.privkey.verify_key
		self.peers = {}
		self.ip_addr = ip_addr
		self.port = port
		self.messages = []
		self.conn, self.cur = connect()
		self.public_key_list = {}
		self.public_key_list[(self.ip_addr,self.port)] = self.pubkey #add community public key to public key list
		self.port_equiv = {}
		self.port_equiv_reverse = {}
		self.miners = []
		self.received_transaction_from = {}
		self.potential_miners = {}
		self.newBlock = ''
		self.txnList = []
		self.pendingBlocks = Queue(1)

		#socket for receiving messages
		self.srcv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.srcv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		print "hostname", self.ip_addr
		print "port", self.port
		self.srcv.bind((self.ip_addr, self.port))
		#add self to list of peers
		self.peers[(self.ip_addr, self.port)] = self.srcv
		checkIfUsersExist(self.conn, self.cur)
		checkIfAdminExist(self.conn, self.cur)
		while find_hashed_password_by_user(ask_for_username(), getpass.getpass(), self.conn, self.cur, 0) != True:
			print "Username or Password is Incorrect. Please try again."
		print "Login Successful"
		Thread(target=self.listening).start()
		Thread(target=self.sending).start()



	def listening(self):
		#listen up to 5 other peers
		self.srcv.listen(5)

		while True:
			read_sockets,write_sockets,error_sockets = select.select(self.peers.values(),[],[],1)
			for socket in read_sockets:

				if socket == self.srcv:
					conn, addr = self.srcv.accept()
					self.peers[addr] = conn
					print "\nEstablished connection with: ", addr
				else:
					#receive the public key from the recently connected peer
					# messages = self.recvall(socket)
					messages = self.recvall(socket)
					recv_buffer = ""
					recv_buffer = recv_buffer + messages
					recv_buffer_split = recv_buffer.split('\0')
					for message in recv_buffer_split[:-1]:
						try:
							json_message = json.loads(message)
							print "\n" + str(socket.getpeername()) + ": " + json.dumps(json_message, indent=4, sort_keys=True)
							category = str(json_message['_category'])
							logger.info("Message received",
								extra={"owner":str(socket.getpeername()), "category": category, "received_message": message})
						except Exception as e:
							logger.error("Invalid format pubkey", exc_info=True)
							print "Invalid format pubkey", e
						
						try:
							if category == str(3):
								self.waitForSignedBlock(socket, json_message)

							elif category == str(4):
								self.addNewPeer(socket, json_message)

							elif category == str(5):
								self.authenticate(socket, json_message)

							elif category == str(9):
								self.collectBlocks(json_message)

							else:
								raise ValueError('No such category')
						except Exception as e:
							logger.error('Category Error', exc_info=True)
							print 'Category Error', e	
	def authenticate(self, socket, json_message):
		print "Authenticating Peer..."
		peer = socket.getpeername()
		credentials = pickle.loads(json_message['content'])
		print credentials[1]
		if find_hashed_password_by_user(str(credentials[0]),str(credentials[1]), self.conn, self.cur):
			print peer[1]
			self.sendMessage(peer[0], peer[1], pickle.dumps(True), 11)
			print "message sent:True"
		else:
			self.sendMessage(peer[0], peer[1], pickle.dumps(False), 11)
			print "message sent:False"

	def recvall(self, socket):
		# Receives all messages until timeout (workaround for receiving part of message only)
		messages = ''
		begin = time.time()
		timeout = 1
		socket.setblocking(0)
		while 1:
			if messages and time.time() - begin > timeout:
				break
			elif time.time() - begin > timeout*2:
				break
			try:
				data = socket.recv(8192)
				if data:
					messages += data
					#change the beginning time for measurement
					begin = time.time()
				else:
					#sleep for sometime to indicate a gap
					time.sleep(0.1)
			except Exception as e:
				pass
		return messages

	def json_serial(self, obj):
		# Serializes datetime object to valid JSON format
		if isinstance(obj, (datetime.datetime, datetime.date)):
			return obj.isoformat()
		raise TypeError("Type %s is not serializable" % type(obj))

	def waitForSignedBlock(self, socket, json_message):
		# proof here
		peer = socket.getpeername()
		if peer in self.port_equiv.keys():
			peer = self.port_equiv[peer]
		if peer in self.received_transaction_from:
			verifier = VerifyKey(HexEncoder.decode(self.received_transaction_from[peer]))
			# self.newBlock = json.loads(json.dumps(self.newBlock))
			if verifier.verify(json_message['content'][0].decode('base64')):
				# parse values
				raw_pubkey = verifier.encode(encoder=HexEncoder)
				p = ''.join([str(ord(c)) for c in raw_pubkey.decode('base64')])
				nonce = json_message['content'][1]
				# get the difference of
				self.potential_miners[peer] = abs(int(self.newBlock['blockHash']+nonce, 36) - int(p[:96], 36))
				# print 'NONCE NI: ', peer
				# print self.potential_miners[peer]

				del self.received_transaction_from[peer]
				logger.info("Block signature verified",
					extra={"hash": hashMe(self.newBlock)})
				print 'Block signature verified: ', hashMe(self.newBlock)
			else:
				logger.warn("Block signature not verified")
				print 'Block signature not verified!'
		else:
			logger.warn("Peer is not in received transactions")
			print 'Peer is not in received transactions!', peer

		# if all blocks are verified
		if len(self.received_transaction_from) == 0:
			#commented out for simulation purposes
			blockNumber = addToChain(self.newBlock, self.conn, self.cur)
			addToTxns(self.txnList, self.conn, self.cur, blockNumber)
			self.messages = []
			self.received_transaction_from = {}

			# broadcast chain
			chain = readChainSql(self.conn, self.cur)
			txns = readTxnsSql(self.conn, self.cur)
			self.broadcastMessage(json.dumps({'chain': chain, 'txns': txns}, default=self.json_serial), 10)
			logger.info('Broadcasted chain and txns',
				extra={'chain': chain, 'txns': txns})

			# get next miner and broadcast
			self.miners = sorted(self.potential_miners)[:(int)(len(self.potential_miners)/3)+1]
			self.pendingBlocks = Queue(len(self.miners))
			for i, self.miner in enumerate(self.miners):
				if self.miner in self.port_equiv.keys():
					self.miners[i] = self.port_equiv[self.miner]
			self.broadcastMessage(self.miners, 5)
			for self.miner in self.miners:
				logger.info("Current miner updated",
					extra={"miner": self.miner})
				print 'Current miner is set to: ', self.miner
			self.potential_miners = {}

	def addNewPeer(self, socket, json_message):
		peer_info = pickle.loads(json_message['content'])
		sender_public_key = VerifyKey(HexEncoder.decode(peer_info[2]))
		self.public_key_list[peer_info[0], peer_info[1]] = sender_public_key
		self.port_equiv[socket.getpeername()] = (peer_info[0], peer_info[1])
		self.port_equiv_reverse[(peer_info[0], peer_info[1])] = socket.getpeername()
		print "_______________"
		print "Public Key List"
		encodedPubKeys = {}
		for addr in self.public_key_list:
			print str(addr) + ':', self.public_key_list[addr].encode(encoder=HexEncoder)
			encodedPubKeys[addr] = self.public_key_list[addr].encode(encoder=HexEncoder)
		print "_______________"
		self.broadcastMessage(pickle.dumps(encodedPubKeys),6)	
		if (self.ip_addr,self.port) in self.public_key_list and len(self.public_key_list) < 3:
			for addr in self.public_key_list:
				if addr != (self.ip_addr, self.port):
					del self.miners[:]
					self.miners.append(addr)
					
					print 'Current miner is set to: ', self.miners	
		if self.miners is not None:
			self.broadcastMessage(self.miners, 5)
			print 'Current miner is set to: ', self.miners

	def collectBlocks(self, json_message):
		content = json.loads(json_message['content'])
		try:
			self.pendingBlocks.put(content,False)
			if self.pendingBlocks.qsize() == len(self.miners):
				content = self.pendingBlocks.get()
				self.pendingBlocks.put(content)
				return self.returnToVerify(content)
		except Exception as e:
			print e

	def returnToVerify(self, content):
		self.newBlock = content['block']
		self.txnList = eval(content['txnList'])
		self.received_transaction_from = eval(content['contributing'])
		for peer in self.received_transaction_from:
			# return block for verification
			if peer in self.port_equiv_reverse.keys():
				self.sendMessage(self.port_equiv_reverse[peer][0], self.port_equiv_reverse[peer][1], json.dumps(self.newBlock), 2)
			else:
				self.sendMessage(peer[0], peer[1], json.dumps(self.newBlock), 2)
			logger.info("Block returned for verification",
				extra={"addr": peer[0], "port": peer[1]})
			print 'Block returned for verification to: ', peer

	def createUser(self):
		checkIfUsersExist(self.conn, self.cur)
		store_info(self.conn, self.cur)

	def resetUsers(self):
		dropUsers(self.conn, self.cur)
	def sending(self):
		while True:
			command = raw_input("Enter command: ")
			if command == "get peers":
				spec_peer = []
				while True:
					inpeers = raw_input("Connect to specific peer(s)?: ")
					if (inpeers == 'q'):
						break
					else:
						try:
							inpeers = inpeers.split(' ')
							spec_peer.append((inpeers[0], int(inpeers[1])))
						except:
							print "Wrong Input: Incomplete Parameters"

				self.getPeers(spec_peer)

			elif command == "send message":
				self.sendMessage()
			elif command == "broadcast message":
				self.broadcastMessage()
			elif command == 'disconnect':
				disconnect(self.conn, self.cur)
			elif command == 'create user':
				self.createUser()
			elif command == 'reset users':
				self.resetUsers()
			else:
				print "Unknown command"

	def __del__(self):
		for conn in self.peers:
			self.peers[conn].close()

	def getPeers(self, peer_addr = []):
		try:
			self.peers[self.community_ip] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.peers[self.community_ip].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self.peers[self.community_ip].bind((self.ip_addr, self.port))
			self.peers[self.community_ip].connect(self.community_ip)
			print "Connected: ", self.community_ip[0], self.community_ip[1]
		except:
			print "Community server down"

	def sendMessage(self, ip=None, port=None, message=None, category=None):
		for addr in self.peers:
			print addr

		while not ip or ip == '':
			ip = raw_input("IP Address: ")

		while not port or port == '':
			port = raw_input("Port: ")
			try:
				port = int(port)
			except Exception as e:
				port = None
				print e

		if (ip, port) in self.peers:
			self.createPacketAndSend(ip, port, message, category)

		elif (ip,port) in self.port_equiv_reverse:
			(ip, port) = self.port_equiv_reverse[(ip, port)]
			self.createPacketAndSend(ip, port, message, category)

		else:
			logger.error("Address not recognized", extra={'IP': ip, 'port': port})
			print "Address not recognized: ", (ip, port)
			raise Exception('Address not recognized')

	def createPacketAndSend(self, ip, port, message, category):
		# replace with actual public key
		if not message:
			message = raw_input("content: ")
		if not category:
			category = raw_input("category: ")
		packet = {u'_owner': self.pubkey.encode(HexEncoder), u'_recipient': 'dummy', u'_category': str(category), u'content':message}
		raw_string = json.dumps(packet)
			
		ssnd = self.peers[(ip,port)]
		try:
			ssnd.sendall(raw_string + '\0')
		except Exception as e:
			logger.error('Send error', exc_info=True)
			print e

	def broadcastMessage(self, message=None, category=None):
		if not message:
			message = raw_input("Message: ")

		if not category:
			category = raw_input("category: ")

		# print self.peers
		for addr in self.peers:
			packet = {u'_owner': self.pubkey.encode(HexEncoder), u'_recipient': 'dummy', u'_category': str(category), u'content':message}
			raw_string = json.dumps(packet)
			if addr != (self.ip_addr, self.port):
				ssnd = self.peers[addr]
				try:
					ssnd.sendall(raw_string + '\0')
				except Exception as e:
					print e

	def returnPeerList(self, ip, port):
		ssnd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		ssnd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		ssnd.bind((self.ip_addr, self.sport))

		try:
			ssnd.connect((ip, port))
			ssnd.sendall(str(self.addrs))
			ssnd.close()
		except Exception as e:
			ssnd.close()
			print e


#main code to run when running peer.py
#include in your input the hostname and the port you want your peer to run in
#example: python peer.py -h 127.0.0.1 -p 6000
#if no arguments passed, will use the default ip and port
def main(argv):
	#this is the default ip and port
	#s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	#s.connect(("8.8.8.8", 80))
	ip_addr = "127.0.0.1"#s.getsockname()[0]
	port = 5000

	try:
		opts, args = getopt.getopt(argv, "h:p:", ["hostname=", "port="])
	except:
		print "Requires hostname and port number"
		sys.exit(2)

	for opt, arg in opts:
		if opt in ("-h", "--hostname"):
			ip_addr = arg
		elif opt in ("-p", "--port"):
			port = int(arg)

	return ip_addr, port

if __name__ == "__main__":
	ip_addr, port = main(sys.argv[1:])

	node = Community_Peer(ip_addr, port)