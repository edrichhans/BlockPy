import json, socket, sys, getopt, select, datetime
from threading import Thread
from main import create, addToChain, connect, disconnect, addToTxns, verifyTxn
from hashMe import hashMe
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_PSS
from Crypto.Hash import SHA256
from Crypto import Random
from uuid import uuid1
import pickle, os, errno
from blockpy_logging import logger
from chain import readChainSql

class Peer(Thread):
	community_ip = ('127.0.0.1', 5000)

	def __init__(self, ip_addr, port, sim=False):
		try:
			os.makedirs('keys')
		except OSError as e:
			if e.errno != errno.EEXIST:
				raise

		try:
			with open("keys/privkey.txt","r") as fpriv:
				key = fpriv.read()
				self.privkey = RSA.importKey(key)
				self.privkey = self.privkey.exportKey()

			with open("keys/pubkey.txt","r") as fpub:
				key = fpub.read()
				self.pubkey = RSA.importKey(key)
				self.pubkey = self.pubkey.exportKey()
		except:
			random_generator = Random.new().read
			self.key = RSA.generate(1024, random_generator)
			self.privkey = self.key.exportKey()
			self.pubkey = self.key.publickey().exportKey()

			with open("keys/pubkey.txt","w") as fpub:
				fpub.write(self.pubkey)
				logger.info("Created public key",
					extra={"publickey": self.pubkey})

			with open("keys/privkey.txt","w") as fpriv:
				fpriv.write(self.privkey)
				logger.info("Created private key")

		self.peers = {}
		self.ip_addr = ip_addr
		self.port = port
		self.received_transaction_from = {}
		self.messages = []
		self.txnList = []
		self.potential_miners = {}
		self.sim = sim
		self.max_txns = 2
		self.conn, self.cur = connect()
		self.miner = None
		self.public_key_list = {}
		self.counter = 0 #for making sure that a newly connected node only connects to other peers once
		#socket for receiving messages
		self.srcv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.srcv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		logger.info("peer.py is running",
			extra={"addr": self.ip_addr, "port": self.port})
		print "hostname", self.ip_addr
		print "port", self.port
		self.srcv.bind((self.ip_addr, self.port))
		#add self to list of peers
		self.peers[(self.ip_addr, self.port)] = self.srcv

		self.getPeers()

		Thread(target=self.listening).start()
		if self.sim==False:
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
					logger.info("Established connection",
						extra={"address": addr})
					print "\nEstablished connection with: ", addr

				else:
					# try:
					recv_buffer = ""
					messages = socket.recv(4096)
					recv_buffer = recv_buffer + messages
					recv_buffer_split = recv_buffer.split('\0')
					print recv_buffer_split
					for message in recv_buffer_split[:-1]:
						if (message.lower() == "reqpeer"):
							peersRequest(socket.getpeername(0), socket.getpeername(1))
						elif (message != ""):
							# 1: waiting for transaction 		2: waiting for verifyBlock Phase
							# 3: waiting for signedBlock Phase	4: waiting for distBlockchain
							if json.loads(message):
								json_message = json.loads(message)
								print "\n" + str(socket.getpeername()) + ": " + json.dumps(json_message, indent=4, sort_keys=True)
								category = str(json_message['_category'])
								logger.info("Message received",
									extra={"owner":str(socket.getpeername()), "category": category, "received_message": message})

								if category == str(1):	#waiting for transaction
									json_message['content'] = RSA.importKey(self.privkey).decrypt(json_message['content'].decode("base64"))
									print json_message
									# message = json.dumps(json_message)

									self.waitForTxn(json_message, socket, message)

								elif category == str(2):	# verifying block
									self.verifyBlock(socket, message)

								elif category == str(3):	#waiting for signedBlock
									self.waitForSignedBlock(socket, json_message)

								elif category == str(5):
									self.miner = json_message['content']
									logger.info("Current miner updated",
										extra={"miner": self.miner})
									print 'Current miner is set to: ', self.miner
									# print 'IP address of miner is: ', self.port
								elif category == str(6):	#peer discovery - update list of public keys
									spec_peer = [] 
									self.public_key_list = pickle.loads(json_message['content'])
									print len(self.public_key_list)
									# if self.community_ip in self.public_key_list and (self.ip_addr,self.port) in self.public_key_list and len(self.public_key_list) < 3:
									# 	self.miner = (self.ip_addr,self.port)
									# 	self.broadcastMessage(self.miner, 5)
									# 	logger.info("Current miner updated",
									# 	extra={"miner": self.miner})
									# 	print 'Current miner is set to: ', self.miner
									if self.counter < 1: #check if peer already had initial connection
										for addr in self.public_key_list: #connect to specific peers not in the local peer list
											if addr not in self.peers:
												spec_peer.append(addr)
										print spec_peer
										self.getPeers(spec_peer, False) #False parameter implies that the peer does not want to reconnect to community peer
										self.counter += 1
									print self.public_key_list
								elif category == str(7): #work around for local port limitations , send public keys of 
									self.public_key_list[socket.getpeername()] = RSA.importKey(pickle.loads(json_message['content'])) #add public key sent by newly connected peer
									print "Public Key List"
									for addr in self.public_key_list:
										print str(addr) + self.public_key_list[addr].exportKey()
									print "_______________"
								elif category == str(8):
									print json_message['content']
								else:
									raise ValueError('No such category')
						else:
							print str(socket.getpeername()), str(socket)
					# except Exception as e:
					# 	print "Data err", e
					# 	del self.peers[socket.getpeername()]
					# 	continue

	# def myconverter(self, o):
	#     if isinstance(o, datetime.datetime):
	#         return o.__str__()

	# def checkTxnExists(self, json_message):
	# 	chain = readChainSql(self.conn, self.cur)
	# 	blockCount = len(chain)
	# 	chain = json.loads(json.dumps(chain,default=self.myconverter))
	# 	for i in range(1,blockCount):
	# 		for j in range(chain[i]['contents']['txnCount']):
	# 			content = json.loads(eval(chain[i]['contents']['blockTxn'])[j]['_content'])
	# 			owner = eval(chain[i]['contents']['blockTxn'])[j]['_owner']
	# 			if json_message['content'] == content and json_message['_owner'] == owner:
	# 				return True
	# 	return False


	def waitForTxn(self, json_message, socket, message):
		try:
			# txnexists = self.checkTxnExists(json_message)
			# if not txnexists:
			owner = json_message['_owner']
			self.received_transaction_from[socket.getpeername()] = owner
			self.messages.append(message)
			if len(self.messages) >= self.max_txns:
				# create new block
				self.newBlock, self.txnList = create(self.messages, self.conn, self.cur)
				for peer in self.received_transaction_from:
					# return block for verification
					self.sendMessage(peer[0], peer[1], json.dumps(self.newBlock), 2)
					logger.info("Block returned for verification",
						extra={"addr": peer[0], "port": peer[1]})
					print 'Block returned for verification to: ', str(peer[0]), str(peer[1])
			# else:
			# 	packet = {u'_category': "8", u'content':"Content already exists! Aborting transaction."}
			# 	raw_string = json.dumps(packet)
			# 	try:
			# 		socket.sendall(raw_string)
			# 	except Exception as e:
			# 		print e
		except Exception as e:
			logger.error("Error sending file", exc_info=True)
			print "SEND ERROR: ", e

	def verifyBlock(self, socket, message):
		# generate nonce
		nonce = uuid1().hex
		# get peer address
		peer = socket.getpeername()
		# get block
		block = json.loads(json.loads(message)['content'])
		# generate fingerprint
		fingerprint = SHA256.new()
		fingerprint.update(json.dumps(block))
		# generate signature
		signer = PKCS1_PSS.new(RSA.importKey(self.privkey))
		signature = signer.sign(fingerprint)
		# send message
		self.sendMessage(peer[0], peer[1], (signature.encode('base64'), nonce), 3)
		logger.info("Signed block sent",
			extra={"addr": peer[0], "port": peer[1]})
		print 'Signed block sent to: ', peer[0], peer[1]

	def waitForSignedBlock(self, socket, json_message):
		# proof here
		peer = socket.getpeername()
		if peer in self.received_transaction_from:
			publickey = RSA.importKey(self.received_transaction_from[peer])
			signer = PKCS1_PSS.new(publickey)
			digest = SHA256.new()
			self.newBlock = json.loads(json.dumps(self.newBlock))
			digest.update(json.dumps(self.newBlock))
			if signer.verify(digest, json_message['content'][0].decode('base64')):
				# parse values
				raw_pubkey = self.received_transaction_from[peer].replace('-----BEGIN PUBLIC KEY-----', '').replace('\n', '').replace('-----END PUBLIC KEY-----', '')
				p = ''.join([str(ord(c)) for c in raw_pubkey.decode('base64')])
				nonce = json_message['content'][1]
				# get the difference of
				self.potential_miners[peer] = abs(int(self.newBlock['blockHash']+nonce, 36) - int(p[:96], 36))
				# print self.potential_miners

				del self.received_transaction_from[peer]
				logger.info("Block signature verified",
					extra={"hash": hashMe(self.newBlock)})
				print 'Block signature verified: ', hashMe(self.newBlock)
			else:
				logger.warn("Block signature not verified")
				print 'Block signature not verified!'
		else:
			logger.warn("Peer is not in received transactions")
			print 'Peer is not in received transactions!'

		# if all blocks are verified
		if len(self.received_transaction_from) == 0:
			#commented out for simulation purposes
			blockNumber = addToChain(self.newBlock, self.conn, self.cur)
			addToTxns(self.txnList, self.conn, self.cur, blockNumber)
			self.messages = []
			self.received_transaction_from = {}

			# get next miner and broadcast
			self.miner = min(self.potential_miners)
			self.broadcastMessage(self.miner, 5)
			logger.info("Current miner updated",
				extra={"miner": self.miner})
			print 'Current miner is set to: ', self.miner

	def sending(self):
		while True:
			command = raw_input("Enter command: ")

			if command == "get peers":

				spec_peer = []

				inpeers = raw_input("Connect to specific peer(s)?: ")
				
				try:
					inpeers = inpeers.split(' ')
					spec_peer.append((inpeers[0], int(inpeers[1])))
				except:
					print "Wrong Input"

				self.getPeers(spec_peer,True)

			elif command == "send":
				self.sendMessage()
			elif command == "broadcast message":
				self.broadcastMessage()
			elif command == 'disconnect':
				disconnect(self.conn, self.cur)
			elif command == 'verify':
				self.getTxn()
			elif command == 'default':
				self.sendToMiner()
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
				logger.info("Connected to community peer",
					extra={"addr":self.community_ip[0], "port":str(self.community_ip[1])})
				print "Connected: ", self.community_ip[0], str(self.community_ip[1])
				message = (self.ip_addr,self.port,self.pubkey)
				self.peers[self.community_ip].sendall(pickle.dumps(message))
			except:
				print "Community server down"

		else:
			for addr in peer_addr:
				self.peers[addr] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				self.peers[addr].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				self.peers[addr].bind((self.ip_addr, 0))
				self.peers[addr].connect(addr)
				logger.info("Connected to peer",
					extra={"addr":addr[0], "port":str(addr[1])})
				print "Connected: ", addr[0], str(addr[1])
				message = (self.pubkey)
				self.sendMessage(addr[0],addr[1],pickle.dumps(message),7) #reply to newly connected peer with public key
				

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

		addr = (ip,port)

		if (ip, port) in self.peers:
			 #replace with actual public key
			if not message:
				message = raw_input("content: ")

			if not category:
				category = input("category: ")

				if not (category>0 and category<9):
					raise ValueError('Category input not within bounds')

			if category == 1:
				random_generator = Random.new().read
				message = self.public_key_list[addr].publickey().encrypt(message,random_generator)[0].encode('base64', 'strict')

			packet = {u'_owner': self.pubkey, u'_recipient': self.public_key_list[addr].exportKey(), u'_category': str(category), u'content':message}
			raw_string = json.dumps(packet)
				
			ssnd = self.peers[(ip,port)]
			try:
				ssnd.sendall(raw_string + '\0')
				return True
			except Exception as e:
				print e
				return False

		else:
			print "Address not recognized"
			return False

	def broadcastMessage(self, message=None, category=None):
		for addr in self.peers:
			print addr

		if not message:
			message = raw_input("Message: ")

		if not category:
			category = raw_input("category: ")

			if not (category>0 and category<9):
					raise ValueError('Category input not within bounds')

		for addr in self.peers:

			if category == 1:
				random_generator = Random.new().read
				message = self.public_key_list[addr].publickey().encrypt(message,random_generator)[0].encode('base64', 'strict')
			
			packet = {u'_owner': self.pubkey, u'_recipient': self.public_key_list[addr].exportKey(), u'_category': str(category), u'content':message}
			raw_string = json.dumps(packet)

			if addr != (self.ip_addr, self.port) and addr != self.community_ip:
				ssnd = self.peers[addr]
				try:
					ssnd.sendall(raw_string + '\0')
				except Exception as e:
					print e

	def getTxn(self, txn=None):
		if txn is None:
			txn = input("Txn number? ")
		else:
			try:
				txn = int(txn)
			except Exception as e:
				logger.error('txn number not recognized',  exc_info=True)
				return False
		try:
			if verifyTxn(txn, self.conn, self.cur):
				logger.info('Transaction #%s verified!', str(txn))
				print 'Transaction #' + str(txn) + ' verified!'
				return True
			else:
				logger.warn('Transaction #%s failed verification!', str(txn))
				print 'Transaction #' + str(txn) + ' failed verification!'
				return False
		except Exception as e:
			logger.error('Verify transaction error',  exc_info=True)
			print 'Verification error:', e
			return False

	def sendToMiner(self, message=None):
		return self.sendMessage(self.miner[0],self.miner[1], message=message, category=1)



#main code to run when running peer.py
#include in your input the hostname and the port you want your peer to run in
#example: python peer.py -h 127.0.0.1 -p 6000
#if no arguments passed, will use the default ip and port
def main(argv):
	#this is the default ip and port
	#s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	#s.connect(("8.8.8.8", 80))
	ip_addr = "127.0.0.1"#s.getsockname()[0]
	port = 8000
	sim = False

	try:
		opts, args = getopt.getopt(argv, "h:p:s:", ["hostname=", "port=", "sim="])
	except:
		print "Requires hostname and port number"
		sys.exit(2)

	for opt, arg in opts:
		if opt in ("-h", "--hostname"):
			ip_addr = arg
		elif opt in ("-p", "--port"):
			port = int(arg)
		elif opt in ("-sim", "--sim"):
			if arg == "t":
				sim = True
			else:
				sim = False

	return ip_addr, port, sim

if __name__ == "__main__":
	ip_addr, port, sim = main(sys.argv[1:])
	node = Peer(ip_addr, port, sim)