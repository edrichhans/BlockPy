
'''

Change ip address and port of commmunity peer before running

'''

import json, socket, sys, getopt, select
from threading import Thread
from main import create, addToChain, connect, disconnect
from hashMe import hashMe
from nacl.encoding import HexEncoder
from nacl.signing import SigningKey, VerifyKey
from uuid import uuid1
import pickle

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
		self.miner = None

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
					#receive the public key from the recently connected peer
					recv_buffer = ""
					messages = socket.recv(4096)
					recv_buffer = recv_buffer + messages
					recv_buffer_split = recv_buffer.split('\0')
					for message in recv_buffer_split:
						try:
							peer_info = pickle.loads(message)
							sender_public_key = VerifyKey(HexEncoder.decode(peer_info[2]))
							self.public_key_list[peer_info[0],peer_info[1]] = sender_public_key
							
							
						# try:
						except:
							print "invalid format pubkey"
						print "_______________"
						print "Public Key List"
						for addr in self.public_key_list:
							print str(addr) + self.public_key_list[addr].encode(encoder=HexEncoder)
						print "_______________"
						encodedKeyList = {}
						for kis in self.public_key_list.keys():
							encodedKeyList[kis] = self.public_key_list[kis].encode(encoder=HexEncoder)
						self.broadcastMessage(pickle.dumps(encodedKeyList),6)	
						if (self.ip_addr,self.port) in self.public_key_list and len(self.public_key_list) < 3:
							for addr in self.public_key_list:
								if addr != (self.ip_addr, self.port):
									self.miner = addr
									
									print 'Current miner is set to: ', self.miner	
						if self.miner is not None:
							self.broadcastMessage(self.miner, 5)
							print 'Current miner is set to: ', self.miner	

						# elif (message != ""):
							#do something with the message
							
						# except Exception as e:
						# 	print "Data err", e
						# 	del self.peers[socket.getpeername()]
						# 	continue

	

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
			else:
				print "Unknown command"


	def __del__(self):
		for conn in self.peers:
			self.peers[conn].close()

	def getPeers(self, peer_addr = []):
		# if (len(peer_addr) == 0 and len(addr) == 0):
			try:
				self.peers[self.community_ip] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				self.peers[self.community_ip].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				self.peers[self.community_ip].bind((self.ip_addr, self.port))
				self.peers[self.community_ip].connect(self.community_ip)
				print "Connected: ", self.community_ip[0], self.community_ip[1]
			except:
				print "Community server down"

		# else:
		# 	for addr in peer_addr:
		# 		self.peers[addr] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		# 		self.peers[addr].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		# 		self.peers[addr].bind((self.ip_addr, 0))
		# 		self.peers[addr].connect(addr)
		# 		print "Connected: ", addr[0], str(addr[1])

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
			
			if not message:
				message = raw_input("content: ")
			if not category:
				category = raw_input("category: ")
			packet = {u'_owner': self.pubkey.encode(encoder=HexEncoder), u'_recipient': 'dummy', u'_category': str(category), u'content':message}
			raw_string = json.dumps(packet)
				
			ssnd = self.peers[(ip,port)]
			try:
				ssnd.sendall(raw_string + '\0')
			except Exception as e:
				print e

		else:
			print "Address not recognized"

	def broadcastMessage(self, message=None, category=None):
		# for addr in self.peers:
		# 	print addr

		if not message:
			message = raw_input("Message: ")

		if not category:
			category = raw_input("category: ")

		# print self.peers
		for addr in self.peers:
			packet = {u'_owner': self.pubkey.encode(encoder=HexEncoder), u'_recipient': 'dummy', u'_category': str(category), u'content':message}
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