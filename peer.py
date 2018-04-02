import json, socket, sys, getopt, select, datetime, heapq, math, time
from threading import Thread
from main import create, addToChain, connect, disconnect, addToTxns, verifyTxn
from hashMe import hashMe
from nacl.encoding import HexEncoder
from nacl.signing import SigningKey, VerifyKey
from nacl.hash import sha256
from uuid import uuid1
import pickle, os, errno
from blockpy_logging import logger
from chain import readChainSql, readTxnsSql


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
				key = HexEncoder.decode(fpriv.read())
				self.privkey = SigningKey(key)

			with open("keys/pubkey.txt","r") as fpub:
				key = HexEncoder.decode(fpub.read())
				self.pubkey = VerifyKey(key)
		except:
			self.privkey = SigningKey.generate()
			self.pubkey = self.privkey.verify_key

			with open("keys/pubkey.txt","w") as fpub:
				fpub.write(self.pubkey.encode(encoder=HexEncoder))
				logger.info("Created public key",
					extra={"publickey": self.pubkey.encode(encoder=HexEncoder)})

			with open("keys/privkey.txt","w") as fpriv:
				fpriv.write(self.privkey.encode(encoder=HexEncoder))
				logger.info("Created private key")

		self.peers = {}
		self.ip_addr = ip_addr
		self.port = port
		self.received_transaction_from = {}
		self.received_transaction_from_reverse = {}
		self.messages = []
		self.txnList = []
		self.potential_miners = {}
		self.sim = sim
		self.max_txns = 4
		self.conn, self.cur = connect()
		self.miners = []
		self.public_key_list = {}
		self.port_equiv = {}
		self.port_equiv_reverse = {}
		self.counter = 0 #for making sure that a newly connected node only connects to other peers once
		#socket for receiving messages
		self.srcv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.srcv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		# self.srcv.settimeout(1)
		# self.srcv.setblocking(0)
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
					messages = self.recvall(socket)
					recv_buffer = ""
					recv_buffer = recv_buffer + messages
					recv_buffer_split = recv_buffer.split('\0')
					for message in recv_buffer_split:
						if (message.lower() == "reqpeer"):
							peersRequest(socket.getpeername(0), socket.getpeername(1))
						elif (message != ""):
							# 1: waiting for transaction 		2: waiting for verifyBlock Phase
							# 3: waiting for signedBlock Phase	4: waiting for distBlockchain
							if json.loads(message):
								json_message = json.loads(message)
								print "\n" + str(socket.getpeername()) + ": category " + json_message['_category']
								category = str(json_message['_category'])
								logger.info("Message received",
									extra={"owner":str(socket.getpeername()), "category": category, "received_message": message})

								if category == str(1):	#waiting for transaction
									json_message['content'] = self.public_key_list[socket.getpeername()].verify(json_message['content'].decode('base64'))
									self.waitForTxn(json_message, socket, message)

								elif category == str(2):	# verifying block
									self.verifyBlock(socket, message)

								elif category == str(3):	#waiting for signedBlock
									self.waitForSignedBlock(socket, json_message)

								elif category == str(5):
									self.miners = json_message['content']
									logger.info("Current miners updated",
										extra={"miners": self.miners})
									print 'Current miners are set to: ', self.miners
								elif category == str(6):	#peer discovery - update list of public keys
									spec_peer = [] 
									templist = pickle.loads(json_message['content'])
									
									if self.counter < 1: #check if peer already had initial connection
										for addr in templist: #connect to specific peers not in the local peer list
											if addr not in self.peers:
												spec_peer.append(addr)
												self.public_key_list[addr] = VerifyKey(HexEncoder.decode(templist[addr]))
												self.port_equiv[addr] = addr
										# print spec_peer
										self.getPeers(spec_peer, False) #False parameter implies that the peer does not want to reconnect to community peer
										self.counter += 1
									print self.public_key_list
								elif category == str(7): #work around for local port limitations , send public keys of 
									addr1 = socket.getpeername()
									addr2 = (pickle.loads(json_message['content'])[1],pickle.loads(json_message['content'])[2])
									self.public_key_list[addr1] = VerifyKey(HexEncoder.decode(pickle.loads(json_message['content'])[0])) #add public key sent by newly connected peer
									self.port_equiv[addr1] = addr2
									self.port_equiv_reverse[addr2] = addr1
									# self.sendMessage(addr2[0], addr2[1], pickle.dumps((self.ip_addr, self.port)), 8)
									print 'REVERSE: ', self.port_equiv_reverse
									print 'REAL: ', self.port_equiv
									print "Public Key List"
									for addr in self.public_key_list:
										print str(addr) + self.public_key_list[addr].encode(encoder=HexEncoder)
									print "_______________"
								elif category == str(8):
									print 'CAT 8: '
									print pickle.loads(json_message['content'])
								elif category == str(10):
									# Received new chain from community peer, check and update tables.
									self.updateTables(json_message)

								else:
									raise ValueError('No such category')
						else:
							print 'End of message.'
					# except Exception as e:
					# 	print "Data err", e
					# 	del self.peers[socket.getpeername()]
					# 	continue

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

	def waitForTxn(self, json_message, socket, message):
		try:
			# txnexists = self.checkTxnExists(json_message)
			# if not txnexists:
			owner = json_message['_owner']
			if socket.getpeername() in self.port_equiv:
				self.received_transaction_from[socket.getpeername()] = owner
				self.received_transaction_from_reverse[self.port_equiv[socket.getpeername()]] = owner
			elif socket.getpeername() in self.port_equiv_reverse:
				self.received_transaction_from_reverse[socket.getpeername()] = owner
				self.received_transaction_from[self.port_equiv_reverse[socket.getpeername()]] = owner
			else:
				logger.error('self.port_equiv not set properly.')
				print 'self.port_equiv not set properly.'

			# print 'REVERSE: ', self.port_equiv, socket.getpeername()
			self.messages.append(message)
			if len(self.messages) >= self.max_txns:
				# create new block
				self.newBlock, self.txnList = create(self.messages, self.conn, self.cur)
				packet = {'block': self.newBlock, 'txnList': str(self.txnList), 'contributing': str(self.received_transaction_from_reverse)}
				self.sendMessage(self.community_ip[0], self.community_ip[1], json.dumps(packet), 9)
				logger.info('Block sent to community peer for collating')
				print 'Block sent to community peer for collating'
		except Exception as e:
			logger.error("Error sending file", exc_info=True)
			print "SEND ERROR: ", e

	def verifyBlock(self, socket, message):
		# generate nonce
		nonce = hashMe(uuid1().hex)
		# get peer address
		peer = socket.getpeername()
		# get block
		block = json.loads(json.loads(message)['content'])
		# generate fingerprint
		fingerprint = sha256
		# generate signature
		signature = self.privkey.sign(fingerprint(json.dumps(block)))
		# send message
		self.sendMessage(peer[0], peer[1], (signature.encode('base64'), nonce), 3)
		logger.info("Signed block sent",
			extra={"addr": peer[0], "port": peer[1]})
		print 'Signed block sent to: ', peer[0], peer[1]

	def waitForSignedBlock(self, socket, json_message):
		# proof here
		peer = socket.getpeername()
		if peer in self.received_transaction_from:
			verifier=self.received_transaction_from[peer]
			self.newBlock = json.loads(json.dumps(self.newBlock))
			if verifier.verify(json_message['content'][0].decode('base64')):
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
			self.received_transaction_from_reverse = {}

			# get next miner and broadcast
			self.miners = sorted(self.potential_miners)[:(int)(len(self.potential_miners)/3)+1]
			for i, self.miner in enumerate(self.miners):
				if self.miner in self.port_equiv.keys():
					print self.port_equiv[self.miner]
					self.miners[i] = self.port_equiv[self.miner]
			self.broadcastMessage(self.miners, 5)
			for self.miner in self.miners:
				logger.info("Current miner updated",
					extra={"miner": self.miner})
				print 'Current miner is set to: ', self.miner

	def updateTables(self, json_message):
		# reset
		self.messages = []
		self.received_transaction_from = {}
		self.received_transaction_from_reverse = {}

		content = json.loads(json_message['content'])
		newChain = content['chain']
		newTxns = content['txns']
		myChain = readChainSql(self.conn, self.cur)
		myTxns = readTxnsSql(self.conn, self.cur)

		# Update table 'blocks'
		for i in range(len(myChain)):
			newTime = newChain[i]['contents']['timestamp']
			if newTime:
				# decode datetime to datatime.datetime() object
				newChain[i]['contents']['timestamp'] = datetime.datetime.strptime(newTime, '%Y-%m-%dT%H:%M:%S.%f')
			if myChain[i] != newChain[i]:
				logger.warn('Block #%s is different from broadcasted chain', i,
					extra={'current': myChain[i], 'new': newChain[i]})
		for i in range(len(myChain), len(newChain)):
			# Add new entries
			blockNumber = addToChain(newChain[i], self.conn, self.cur)

		logger.info('Updated current chain!',
			extra={'NewBlocks': newChain[len(myChain):]})

		# Update table 'txns'
		for i in range(len(myTxns)):
			newTime = newTxns[i]['timestamp']
			if newTime:
				# decode datetime to datatime.datetime() object
				newTxns[i]['timestamp'] = datetime.datetime.strptime(newTime, '%Y-%m-%dT%H:%M:%S.%f')
			if myTxns[i] != newTxns[i]:
				logger.warn('Transaction #%s is different from broadcasted txns', i,
					extra={'current': myTxns[i], 'new': newTxns[i]})
		for i in range(len(myTxns), len(newTxns)):
			newTxn = newTxns[i]
			# Add new entries
			addToTxns([newTxn['content']], self.conn, self.cur, newTxn['blockNumber'], newTxn['txnNumber'], \
				datetime.datetime.strptime(newTxn['timestamp'], '%Y-%m-%dT%H:%M:%S.%f'))

		logger.info('Updated txns!',
			extra={'NewTxns': newTxns[len(myTxns):]})

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
				message = raw_input('content: ')
				self.sendToMiners(message)
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
				# self.peers[self.community_ip].settimeout(1)	# set timeout for recv()
				# self.peers[self.community_ip].setblocking(0)	# set socket to non-blocking mode
				self.peers[self.community_ip].bind((self.ip_addr,0))
				self.peers[self.community_ip].connect(self.community_ip)
				logger.info("Connected to community peer",
					extra={"addr":self.community_ip[0], "port":str(self.community_ip[1])})
				print "Connected: ", self.community_ip[0], str(self.community_ip[1])
				print "here1"
				message = (self.ip_addr,self.port,self.pubkey.encode(encoder=HexEncoder))
				self.sendMessage(self.community_ip[0], self.community_ip[1], pickle.dumps(message), 4)
				print "here"
			except Exception as e:
				logger.error('Community Server Error', exc_info=True)
				print 'Community Server Error: ', e

		else:
			for addr in peer_addr:
				self.peers[addr] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				self.peers[addr].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				# self.peers[addr].settimeout(1)
				# self.peers[addr].setblocking(0)
				self.peers[addr].bind((self.ip_addr, 0))
				self.peers[addr].connect(addr)
				logger.info("Connected to peer",
					extra={"addr":addr[0], "port":str(addr[1])})
				print "Connected: ", addr[0], str(addr[1])
				message = (self.pubkey.encode(encoder=HexEncoder))
				self.sendMessage(addr[0], addr[1], pickle.dumps((message,self.ip_addr,self.port)), 7) #reply to newly connected peer with public key
				

	def sendMessage(self, ip=None, port=None, message=None, category=None):
		for addr in self.public_key_list:
			print addr,":",self.public_key_list[addr].encode(encoder=HexEncoder)

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

		if addr in self.peers:
			return self.createPacketAndSend(addr, ip, port, message, category)

		elif addr in self.port_equiv_reverse:
			addr = self.port_equiv_reverse[addr]
			return self.createPacketAndSend(addr, ip, port, message, category)

		else:
			print "Address not recognized: "
			print "IP: ", ip
			print "Port: ", port
			print self.port_equiv
			return False

	def createPacketAndSend(self, addr, ip, port, message, category):
		 #replace with actual public key
		if not message:
			message = raw_input("content: ")

		if not category:
			category = input("category: ")

			if not (category>0 and category<9):
				raise ValueError('Category input not within bounds')

		if category == 1:
			if addr in self.public_key_list:
				key = self.public_key_list[addr]
			elif addr in self.port_equiv_reverse and self.port_equiv_reverse[addr] in self.public_key_list:
				key = self.public_key_list[self.port_equiv_reverse[addr]]
			elif addr in self.port_equiv and self.port_equiv[addr] in self.public_key_list:
				key = self.public_key_list[self.port_equiv[addr]]

			hasher = sha256
			message = self.privkey.sign(hasher(message)).encode('base64')

		if addr == self.community_ip:
			packet = {u'_owner': self.pubkey.encode(HexEncoder), u'_recipient': self.community_ip, u'_category': str(category), u'content':message}
		else:
			packet = {u'_owner': self.pubkey.encode(HexEncoder), u'_recipient': self.public_key_list[addr].encode(encoder=HexEncoder), u'_category': str(category), u'content':message}
		raw_string = json.dumps(packet)
			
		ssnd = self.peers[addr]
		try:
			ssnd.sendall(raw_string + '\0')
			return True
		except Exception as e:
			print e
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

		for addr in self.public_key_list:

			if category == 1:
				hasher = sha256
				message = self.privkey.sign(hasher(message)).encode('base64')
				
			packet = {u'_owner': self.pubkey.encode(HexEncoder), u'_recipient': self.public_key_list[addr].encode(encoder=HexEncoder), u'_category': str(category), u'content':message}
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

	def sendToMiners(self, message=None):
		for self.miner in self.miners:
			if self.miner in self.port_equiv_reverse.keys():
				if not self.sendMessage(self.port_equiv_reverse[self.miner][0],self.port_equiv_reverse[self.miner][1], message=message, category=1):
					return False
			else:
				if not self.sendMessage(self.miner[0],self.miner[1], message=message, category=1):
					return False
		return True



#main code to run when running peer.py
#include in your input the hostname and the port you want your peer to run in
#example: python peer.py -h 127.0.0.1 -p 6000
#if no arguments passed, will use the default ip and port
def main(argv):
	#this is the default ip and port
	#s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	#s.connect(("8.8.8.8", 80))
	ip_addr = "127.0.0.1"	# s.getsockname()[0]
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