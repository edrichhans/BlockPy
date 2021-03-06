import json, socket, sys, getopt, select, datetime, time, os, errno
from threading import Thread
from main import create, addToChain, connect, disconnect, addToTxns, verifyTxn, updateChain, updateTxns
from hashMe import hashMe
from nacl.encoding import HexEncoder
from nacl.signing import SigningKey, VerifyKey
from nacl.hash import sha256
from uuid import uuid1
from blockpy_logging import logger
from chain import readChainSql, readTxnsSql
from login import ask_for_username, ask_for_password
import getpass, hashlib

class Peer(Thread):
	_FINISH = True

	def __init__(self, ip_addr, port, sim=False, community_ip='10.147.20.127', community_port=5000, username=None, password=None):
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

		self.community_ip = (community_ip, community_port)
		self.username = username
		self.password = password
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
		self.counter = 0 #for making sure that a newly connected node only connects to other peers once
		#socket for receiving messages
		self.authenticated = False
		self.waitForAuth = False
		self.srcv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.srcv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		logger.info("peer.py is running",
			extra={"addr": self.ip_addr, "port": self.port})
		print "hostname", self.ip_addr
		print "port", self.port
		self.srcv.bind((self.ip_addr, self.port))
		#add self to list of peers
		self.peers[(self.ip_addr, self.port)] = self.srcv
		self.is_miner = False
		self.ack = False
		self.getPeers()

		self.lthread = Thread(target=self.listening)
		self.lthread.start()

		while(self.authenticated==False):
			if self.waitForAuth == False:
				self.getAuth()
		self.getPeers()

		if self.sim == False:
			self.sthread = Thread(target=self.sending)
			self.sthread.start()

	def listening(self):
		#listen up to 5 other peers
		self.srcv.listen(10)
		while self._FINISH:
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
						if (message != ""):
							# 1: waiting for transaction 		2: waiting for verifyBlock Phase
							# 3: waiting for signedBlock Phase	4: waiting for distBlockchain
							try:
								json_message = json.loads(message)
								print "\n" + str(socket.getpeername()) + ": category " + json_message['_category']
								category = str(json_message['_category'])
								logger.info("Message received",
									extra={"owner":str(socket.getpeername()), "category": category, "received_message": message})

								if category == str(1):	#waiting for transaction
									json_message['content'] = self.public_key_list[socket.getpeername()].verify(json_message['content'].decode('base64'))
									self.waitForTxn(json_message, socket)

								elif category == str(2):	# verifying block
									self.verifyBlock(socket, message)

								elif category == str(5):
									self.miners=[]
									self.is_miner = False
									for miner in json_message['content']:
										if (miner[0],miner[1]) == (self.ip_addr,self.port):
											self.is_miner = True
										else:
											self.miners.append((miner[0],miner[1]))
									logger.info("Current miners updated",
										extra={"miners": self.miners})
									print 'Current miners are set to: ', self.miners

								elif category == str(6):	#peer discovery - update list of public keys
									spec_peer = [] 
									templist = json.loads(json_message['content'])
									
									if self.counter < 1: #check if peer already had initial connection
										for addr in templist: #connect to specific peers not in the local peer list
											print templist[addr]
											addr1 = eval(addr)
											if addr1 not in self.peers:
												spec_peer.append(addr1)
												self.public_key_list[addr1] = VerifyKey(HexEncoder.decode(templist[addr]))
												self.port_equiv[addr1] = addr1
										#False parameter implies that the peer does not want to reconnect to community peer
										self.getPeers(spec_peer, False)
										self.counter += 1
									print self.public_key_list

								elif category == str(7): 
									addr1 = socket.getpeername()
									addr2 = (json.loads(json_message['content'])[1],json.loads(json_message['content'])[2])
									#add public key sent by newly connected peer
									self.public_key_list[addr1] = VerifyKey(HexEncoder.decode(json.loads(json_message['content'])[0]))
									self.port_equiv[addr1] = addr2
									print "Public Key List"
									for addr in self.public_key_list:
										print str(addr) + ':', self.public_key_list[addr].encode(encoder=HexEncoder)
									print "_______________"

								elif category == str(8):
									print 'CAT 8: '
									print json.loads(json_message['content'])

								elif category == str(10):
									# Received new chain from community peer, check and update tables.
									self.updateTables(json_message)

								elif category == str(11):
									print "Received Auth response"
									self.getAuth(json_message)

								elif category == str(12):
									self.ack = json_message['content']
									print 'ACK Received:', self.ack
									logger.info('ACK Received',
										extra={'ack': self.ack})

								else:
									raise ValueError('No such category')
							except:
								logger.error('JSON.loads message error')
								print 'JSON.loads message error'
						else:
							print 'End of message.'

	def recvall(self, socket):
		# Receives all messages until timeout (workaround for receiving part of message only)
		messages = ''
		begin = time.time()
		timeout = 0.1
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
					time.sleep(0.05)
			except Exception as e:
				pass
		return messages

	def waitForTxn(self, json_message, socket = None):
		try:
			owner = json_message['_owner']
			peer = None
			#if self is miner and not in miner list, simpler solution
			if socket is None and self.is_miner:
				self.received_transaction_from[(self.ip_addr, self.port)] = owner
				self.received_transaction_from_reverse[(self.ip_addr, self.port)] = owner
			else:
				peer = socket.getpeername()
				if peer in self.port_equiv:
					self.received_transaction_from[peer] = owner
					self.received_transaction_from_reverse[self.port_equiv[peer]] = owner
				elif peer in self.port_equiv.values():
					for key,value in self.port_equiv.items():
						if peer == value:
							self.received_transaction_from_reverse[value] = owner
							self.received_transaction_from[key] = owner
				else:
					logger.error('self.port_equiv not set properly.')
					print 'self.port_equiv not set properly.'

			if len(self.messages) < self.max_txns:
				self.messages.append(json_message)
				if peer:
					self.peers[peer].send(self.sendMessage(None, json_message['content'], 12))
					logger.info('ACK sent to %s', str(peer))
					print 'ACK sent to:', peer, json_message['content']
				else:
					self.ack = json_message['content']
					logger.info('ACK sent to self',
						extra={'ack': self.ack})
					print 'ACK sent to self', self.ack
				if len(self.messages) >= self.max_txns:
					# create new block
					self.newBlock, self.txnList = create(self.messages, self.conn, self.cur)
					logger.info('Block generated',
						extra={'blockHash': self.newBlock['blockHash'], 'txnList': self.txnList})
					packet = {'block': self.newBlock, 'txnList': str(self.txnList), 'contributing': str(self.received_transaction_from_reverse)}
					self.peers[self.community_ip].send(self.sendMessage(None,json.dumps(packet), 9))
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
		# generate signature
		signature = self.privkey.sign(str(hashMe(json.dumps(block))))
		# send message
		self.peers[peer].send(self.sendMessage(None, (signature.encode('base64'), nonce), 3))
		logger.info("Signed block sent",
			extra={"addr": peer[0], "port": peer[1], "blockHash": block['blockHash']})
		print 'Signed block sent to: ', peer[0], peer[1]

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
				logger.warn('Block #%s is different from broadcasted chain', i+1,
					extra={'current': myChain[i], 'new': newChain[i]})
				updateChain(i+1, newChain[i], self.conn, self.cur)
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
				logger.warn('Transaction #%s is different from broadcasted txns', i+1,
					extra={'current': myTxns[i], 'new': newTxns[i]})
				newTxn = newTxns[i]
				updateTxns(newTxn['content'], self.conn, self.cur, newTxn['blockNumber'], i+1, \
					datetime.datetime.strptime(str(newTxn['timestamp']), '%Y-%m-%d %H:%M:%S.%f'))
		for i in range(len(myTxns), len(newTxns)):
			newTxn = newTxns[i]
			# Add new entries
			addToTxns([newTxn['content']], self.conn, self.cur, newTxn['blockNumber'], newTxn['txnNumber'], \
				datetime.datetime.strptime(str(newTxn['timestamp']), '%Y-%m-%dT%H:%M:%S.%f'))

		logger.info('Updated txns!',
			extra={'NewTxns': newTxns[len(myTxns):]})

	def sending(self):

		while self._FINISH:
			command = raw_input("Enter command: ")
			if command == "send":
				self.sendToMiners()
			elif command == "broadcast message":
				self.broadcastMessage()
			elif command == 'disconnect':
				disconnect(self.conn, self.cur)
				self._FINISH = False
			elif command == 'verify':
				self.getTxn()
			elif command == 'default':
				message = raw_input('content: ')
				self.sendToMiners("dummy",message)
			else:
				print "Unknown command"

	def endPeer(self):
		disconnect(self.conn, self.cur)
		self._FINISH = False

	def __del__(self):
		for conn in self.peers:
			self.peers[conn].close()

	def getPeers(self, peer_addr = [], connect_to_community_peer = True):
		if (len(peer_addr) == 0 and connect_to_community_peer):
			try:
				if(self.authenticated == False):
					self.peers[self.community_ip] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					self.peers[self.community_ip].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
					self.peers[self.community_ip].bind((self.ip_addr,0))
					self.peers[self.community_ip].connect(self.community_ip)
					logger.info("Connected to community peer",
						extra={"addr":self.community_ip[0], "port":str(self.community_ip[1])})
					print "Connected: ", self.community_ip[0], str(self.community_ip[1])
				else:
					message = (self.ip_addr,self.port,self.pubkey.encode(encoder=HexEncoder))
					self.peers[self.community_ip].send(self.sendMessage(None, json.dumps(message), 4))
			except Exception as e:
				logger.error('Community Server Error', exc_info=True)
				print 'Community Server Error: ', e
		else:
			for addr in peer_addr:
				self.peers[addr] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				self.peers[addr].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				self.peers[addr].bind((self.ip_addr, 0))
				self.peers[addr].connect(addr)
				logger.info("Connected to peer",
					extra={"addr":addr[0], "port":str(addr[1])})
				print "Connected: ", addr[0], str(addr[1])
				message = (self.pubkey.encode(encoder=HexEncoder))
				self.peers[addr].send(self.sendMessage(None,json.dumps((message,self.ip_addr,self.port)),7)) #reply to newly connected peer with public key

	def sendMessage(self, recpubkey=None, message=None, category=None):
		 #replace with actual public key
		
		if not message:
			message = raw_input("content: ")

		if not category:
			category = input("category: ")

		if category == 1:

			if not recpubkey:
				recpubkey = raw_input("public key of receiver: ")

			message = self.privkey.sign(str(hashMe(message))).encode('base64')
			
		packet = {u'_owner': self.pubkey.encode(encoder=HexEncoder), u'_recipient': recpubkey, u'_category': str(category), u'content':message}
		raw_string = json.dumps(packet)
			
		return raw_string + '\0'

	def broadcastMessage(self, recpubkey=None, message=None, category=None):
		raw_string = self.sendMessage(recpubkey,message,category)
		for addr in self.peers:
			if addr != (self.ip_addr, self.port) and addr != self.community_ip:
				try:
					self.peers[addr].send(raw_string)
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
				return {txn: True}
			else:
				logger.warn('Transaction #%s failed verification!', str(txn))
				print 'Transaction #' + str(txn) + ' failed verification!'
				return {txn: False}
		except Exception as e:
			logger.error('Verify transaction error',  exc_info=True)
			print 'Verification error:', e
			return {txn: False}

	def sendToMiners(self, recpubkey=None, message=None):
		begin = 0
		# set ACK timeout to 3 seconds before resending
		timeout = 3
		expectedAck = hashMe(message)
		while not self.ack == expectedAck:
			logger.info('Sending transaction',
				extra={'contents': message})
			print 'Sending transaction:', message
			begin = time.time()
			raw_string = self.sendMessage(recpubkey,message,1)
			for miner in self.miners:
				if miner in self.port_equiv.values():
					for key,value in self.port_equiv.items():
						if miner == value:
							if not self.peers[key].send(raw_string):
								return False
				else:
					if not self.peers[miner].send(raw_string):
						return False
			#Handling if self is miner, after sending to other miners, trigger waitForTxn			
			if self.is_miner:
				raw_string = self.sendMessage(self.pubkey.encode(HexEncoder),message,1)[:-1] #remove '\0' delimeter
				json_message = json.loads(raw_string)
				category = str(json_message['_category'])
				# Bypass encryption if self mining
				json_message['content'] = hashMe(message)
				logger.info("Mining message from self",
					extra={"owner":str((self.ip_addr,self.port)), "category": category, "received_message": raw_input})
				if category == str(1):	#waiting for transaction
					# send to self
					self.waitForTxn(json_message)
			while time.time() - begin < timeout:
				if self.ack == expectedAck:
					break
				elif self.ack and self.ack != expectedAck:
					print 'ACK and expected ACK mismatch'
					logger.warn('ACK and expected ACK mismatch',
						extra={'ack': self.ack, 'expectedAck': expectedAck})
				# Check for an ACK every 0.1 secs
				time.sleep(0.1)

		print 'Valid ACK received:', self.ack
		logger.info('Valid ACK received',
			extra={'ack': self.ack})
		self.ack = False
		return True

	def getAuth(self,json_message = None):
		username = self.username
		password = self.password
		hashed_password = None
		if json_message is not None:
			self.authenticated = json.loads(json_message['content'])
			print self.authenticated
		print "Authenticating....."
		if self.authenticated:
			print "Login Successful"
		else:
			self.waitForAuth = True
			if not username:
				username = ask_for_username()
			if not password:
				hashed_password = hashlib.sha256(getpass.getpass()).hexdigest()
			else:
				hashed_password = hashlib.sha256(password).hexdigest()
			message = (username, hashed_password)
			self.peers[self.community_ip].send(self.sendMessage(None, json.dumps(message), 5))

	def getPeersAPI(self):
		return self.peers.keys()

#main code to run when running peer.py
#include in your input the hostname and the port you want your peer to run in
#example: python peer.py -h 127.0.0.1 -p 6000
#if no arguments passed, will use the default ip and port
def main(argv):
	#this is the default ip and port
	#s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	#s.connect(("8.8.8.8", 80))
	ip_addr = "10.147.20.65"	# s.getsockname()[0]
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