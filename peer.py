import json, socket, sys, getopt, select
from threading import Thread
from main import create, addToChain, connect, disconnect
from hashMe import hashMe
from Crypto.PublicKey import RSA
from Crypto import Random
from uuid import uuid1
import pickle

class Peer(Thread):
	community_ip = ('127.0.0.1', 5000)

	def __init__(self, ip_addr, port):
		random_generator = Random.new().read
		self.key = RSA.generate(1024, random_generator)
		self.peers = {}
		self.ip_addr = ip_addr
		self.port = port
		self.received_transaction_from = {}
		self.messages = []
		self.max_txns = 2
		self.conn, self.cur = connect()
		self.potential_miners = {}
		self.miner = None
		self.public_key_list = {}
		self.counter = 0 #for making sure that a newly connected node only connects to other peers once

		#socket for receiving messages
		self.srcv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.srcv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		print "hostname", self.ip_addr
		print "port", self.port
		self.srcv.bind((self.ip_addr, self.port))
		#add self to list of peers
		self.peers[(self.ip_addr, self.port)] = self.srcv

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
					# try:
					message = socket.recv(4096)

					if (message == "Requesting peers sir"):
						peersRequest(socket.getpeername(0), socket.getpeername(1))
					elif (message != ""):
						# 1: waiting for transaction 		2: waiting for verifyBlock Phase
						# 3: waiting for signedBlock Phase	4: waiting for distBlockchain
						if json.loads(message):
							json_message = json.loads(message)
							print "\n" + str(socket.getpeername()) + ": " + message
							category = str(json_message['_category'])
							if category == str(1):	#waiting for transaction
								# self.waitForTxn(json_message, socket, message)
								None

							elif category == str(2):	# verifying block
								# self.verifyBlock(socket, message)
								None
							elif category == str(3):	#waiting for signedBlock
								self.waitForSignedBlock(socket, json_message)

							elif category == str(5):
								self.miner = json_message['content']
								print 'Current miner is set to: ', self.miner

							elif category == str(6):	#peer discovery - update list of public keys
								spec_peer = [] 
								self.public_key_list = pickle.loads(json_message['content'])
								if self.counter < 1: #check if peer already had initial connection
									for addr in self.public_key_list: #connect to specific peers not in the local peer list
										if addr not in self.peers:
											spec_peer.append(addr)
									print spec_peer
									self.getPeers(spec_peer, False) #False parameter implies that the peer does not want to reconnect to community peer
									self.counter += 1
								# print self.public_key_list
					else:
						print str(socket.getpeername()), str(socket)
					# except Exception as e:
					# 	print "Data err", e
					# 	del self.peers[socket.getpeername()]
					# 	continue

	def waitForTxn(self, json_message, socket, message):
		try:
			owner = json_message['_owner']
			self.received_transaction_from[socket.getpeername()] = owner
			self.messages.append(message)
			if len(self.messages) >= self.max_txns:
				self.newBlock = create(self.messages, self.conn, self.cur)
				for peer in self.received_transaction_from:
					self.sendMessage(peer[0], peer[1], json.dumps(self.newBlock), 2)
					print 'Block sent to: ', str(peer[0]), str(peer[1])
		except Exception as e:
			print "SEND ERROR: ", e

	def verifyBlock(self, socket, message):
		# generate nonce
		nonce = uuid1().hex
		# get peer address
		peer = socket.getpeername()
		# get block
		block = json.loads(json.loads(message)['content'])
		# generate fingerprint
		fingerprint = hashMe(block).encode('utf-8')
		# generate signature
		signature = self.key.sign(fingerprint, '')
		# send message
		self.sendMessage(peer[0], peer[1], signature + (nonce,), 3)
		print 'Block sent to: ', peer[0], peer[1]

	def waitForSignedBlock(self, socket, json_message):
		# proof here
		peer = socket.getpeername()
		if peer in self.received_transaction_from:
			publickey = RSA.importKey(self.received_transaction_from[peer])
			if publickey.verify(hashMe(self.newBlock).encode('utf-8'), (json_message['content'][0],)):
				# parse values
				raw_pubkey = self.received_transaction_from[peer].replace('-----BEGIN PUBLIC KEY-----', '').replace('\n', '').replace('-----END PUBLIC KEY-----', '')
				p = ''.join([str(ord(c)) for c in raw_pubkey.decode('base64')])
				nonce = json_message['content'][1]
				# get the difference of
				self.potential_miners[peer] = abs(int(self.newBlock['blockHash']+nonce, 36) - int(p[:96], 36))
				print self.potential_miners

				del self.received_transaction_from[peer]
				print 'Block signature verified: ', hashMe(self.newBlock)
			else:
				print 'Block signature not verified!'
		else:
			print 'Peer is not in received transactions!'

		# if all blocks are verified
		if len(self.received_transaction_from) == 0:
			addToChain(self.newBlock, self.conn, self.cur)
			self.messages = []
			self.received_transaction_from = {}

			# get next miner and broadcast
			self.miner = min(self.potential_miners)
			self.broadcastMessage(self.miner, 5)
			print 'Current miner is set to: ', self.miner

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

				self.getPeers(spec_peer, True)

			elif command == "send message":
				self.sendMessage()
			elif command == "broadcast message":
				self.broadcastMessage()
			elif command == 'disconnect':
				disconnect(self.conn, self.cur)
			else:
				print "Unknown command"


	def __del__(self):
		for conn in self.peers:
			self.peers[conn].close()

	def getPeers(self, peer_addr = [],connect_to_community_peer = True):
		if (len(peer_addr) == 0 and connect_to_community_peer):
			try:
				self.peers[self.community_ip] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				self.peers[self.community_ip].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				self.peers[self.community_ip].bind((self.ip_addr,0))
				self.peers[self.community_ip].connect(self.community_ip)
				print "Connected: ", self.community_ip[0], str(self.community_ip[1])
				message = (self.ip_addr,self.port,self.key.publickey().exportKey())
				self.peers[self.community_ip].sendall(pickle.dumps(message))
			except:
				print "Community server down"

		else:
			for addr in peer_addr:
				self.peers[addr] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				self.peers[addr].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				self.peers[addr].bind((self.ip_addr, 0))
				self.peers[addr].connect(addr)
				print "Connected: ", addr[0], str(addr[1])
				

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
			pubkey = self.key.publickey().exportKey()
			# pubkey = pubkey.encode('string_escape').replace('\\\\','\\')
			 #replace with actual public key
			if not message:
				message = raw_input("content: ")
			if not category:
				category = raw_input("category: ")
			packet = {u'_owner': pubkey, u'_recipient': 'dummy', u'_category': str(category), u'content':message}
			raw_string = json.dumps(packet)
				
			ssnd = self.peers[(ip,port)]
			try:
				ssnd.sendall(raw_string)
			except Exception as e:
				print e

		else:
			print "Address not recognized"

	def broadcastMessage(self, message=None, category=None):
		for addr in self.peers:
			print addr

		pubkey = self.key.publickey().exportKey()
		if not message:
			message = raw_input("Message: ")

		if not category:
			category = raw_input("category: ")

		packet = {u'_owner': pubkey, u'_recipient': 'dummy', u'_category': str(category), u'content':message}
		raw_string = json.dumps(packet)
		for addr in self.peers:
			if addr != (self.ip_addr, self.port) and addr != self.community_ip:
				ssnd = self.peers[addr]
				try:
					ssnd.sendall(raw_string)
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
	ip_addr = '127.0.0.1'
	port = 8000

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

	node = Peer(ip_addr, port)