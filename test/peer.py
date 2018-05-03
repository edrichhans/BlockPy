import json, socket, sys, getopt, select, datetime, time, os, errno
from threading import Thread
from main import create, addToChain, connect, disconnect, addToTxns, verifyTxn
from hashMe import hashMe
from nacl.encoding import HexEncoder
from nacl.signing import SigningKey, VerifyKey
from nacl.hash import sha256
from uuid import uuid1
from blockpy_logging import logger
from chain import readChainSql, readTxnsSql
from login import ask_for_username, ask_for_password
import getpass

class Peer(Thread):
	community_ip = ('127.0.0.1', 5000)
	_FINISH = False

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
		self.getPeers()

		self.lthread = Thread(target=self.listening)
		self.lthread.daemon = True
		self.lthread.start()
		if self.sim == False:
			self.sthread = Thread(target=self.sending)
			self.sthread.daemon = True
			self.sthread.start()

		while (1):
			try:
				if self._FINISH:
					break
			except(KeyboardInterrupt, SystemExit):
				break

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
						if (message != ""):
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

								elif category == str(5):
									self.miners=[]
									for miner in json_message['content']:
										self.miners.append((str(miner[0]),miner[1]))
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
										self.getPeers(spec_peer, False) #False parameter implies that the peer does not want to reconnect to community peer
										self.counter += 1
									print self.public_key_list
								elif category == str(7): 
									addr1 = socket.getpeername()
									addr2 = (json.loads(json_message['content'])[1],json.loads(json_message['content'])[2])
									self.public_key_list[addr1] = VerifyKey(HexEncoder.decode(json.loads(json_message['content'])[0])) #add public key sent by newly connected peer
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

								else:
									raise ValueError('No such category')
						else:
							print 'End of message.'

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
			owner = json_message['_owner']
			if socket.getpeername() in self.port_equiv:
				self.received_transaction_from[socket.getpeername()] = owner
				self.received_transaction_from_reverse[self.port_equiv[socket.getpeername()]] = owner
			elif socket.getpeername() in self.port_equiv.values():
				for key,value in self.port_equiv.items():
					if socket.getpeername() == value:
						self.received_transaction_from_reverse[value] = owner
						self.received_transaction_from[key] = owner
			else:
				logger.error('self.port_equiv not set properly.')
				print 'self.port_equiv not set properly.'

			self.messages.append(message)
			if len(self.messages) >= self.max_txns:
				# create new block
				self.newBlock, self.txnList = create(self.messages, self.conn, self.cur)
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
		# generate fingerprint
		fingerprint = sha256
		# generate signature
		signature = self.privkey.sign(fingerprint(json.dumps(block)))
		# send message
		self.peers[peer].send(self.sendMessage(None, (signature.encode('base64'), nonce), 3))
		logger.info("Signed block sent",
			extra={"addr": peer[0], "port": peer[1]})
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
		while(self.authenticated==False):
			if self.waitForAuth == False:
				self.getAuth()
		self.getPeers()
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

				self.getPeers(spec_peer,False)

			elif command == "send":
				self.sendToMiners()
			elif command == "broadcast message":
				self.broadcastMessage()
			elif command == 'disconnect':
				disconnect(self.conn, self.cur)
				self._FINISH = True
			elif command == 'verify':
				self.getTxn()
			elif command == 'default':
				message = raw_input('content: ')
				self.sendToMiners("dummy",message)
			else:
				print "Unknown command"


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

			if not (category>0 and category<9):
				raise ValueError('Category input not within bounds')

		if category == 1:

			if not recpubkey:
				recpubkey = raw_input("public key of receiver: ")

			hasher = sha256
			message = self.privkey.sign(hasher(message)).encode('base64')
			
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
				return True
			else:
				logger.warn('Transaction #%s failed verification!', str(txn))
				print 'Transaction #' + str(txn) + ' failed verification!'
				return False
		except Exception as e:
			logger.error('Verify transaction error',  exc_info=True)
			print 'Verification error:', e
			return False

	def sendToMiners(self, recpubkey=None, message=None):
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
		return True

	def getAuth(self,json_message = None): 
		if json_message is not None:
			self.authenticated = json.loads(json_message['content'])
			print self.authenticated
		print "Authenticating....."
		if self.authenticated:
			print "Login Successful"
		else:
			self.waitForAuth = True
			message = (ask_for_username(),getpass.getpass())
			self.peers[self.community_ip].send(self.sendMessage(None, json.dumps(message), 5))

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