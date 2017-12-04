import json, socket, sys, getopt, select
from threading import Thread
from main import create

class Peer(Thread):

	community_ip = ('127.0.0.1', 5000)

	def __init__(self, ip_addr, port):

		self.peers = {}
		self.ip_addr = ip_addr
		self.port = port

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
					message = socket.recv(1024)

					if (message == "Requesting peers sir"):
						peersRequest(socket.getpeername(0), socket.getpeername(1))
					elif (message != ""):
						try:
							create(message)
						except:
							print "MESSAGE NOT WORKING"
						print create
						print "\n" + str(socket.getpeername()) + ": " + message
					else:
						print str(socket.getpeername()), str(socket)
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
			elif command == "quit":
				exit()
			else:
				print "Unknown command"


	def __del__(self):
		for conn in self.peers:
			self.peers[conn].close()

	def getPeers(self, peer_addr = []):

		if (len(peer_addr) == 0 and len(addr) == 0):
			try:
				self.peers[self.community_ip] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				self.peers[self.community_ip].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				self.peers[self.community_ip].bind((self.ip_addr, self.port))
				self.peers[self.community_ip].connect(self.community_ip)
				print "Connected: ", self.community_ip[0], self.community_ip[1]
			except:
				print "Community server down"

		else:
			for addr in peer_addr:
				self.peers[addr] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				self.peers[addr].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				self.peers[addr].bind((self.ip_addr, 0))
				self.peers[addr].connect(addr)
				print "Connected: ", addr[0], str(addr[1])

	def sendMessage(self):

		for addr in self.peers:
			print addr

		while True:
			ip = raw_input("IP Address: ")

			if ip == '':
				print "Enter IP Address"
			else:
				break

		while True:
			port = input("Port: ")

			if port == '':
				print "Enter Port"
			else:
				break

		if (ip, port) in self.peers:

			message = raw_input("Message: ")
			ssnd = self.peers[(ip,port)]

			try:
				ssnd.sendall(message)
			except Exception as e:
				print e

		else:
			print "Address not recognized"

	def broadcastMessage(self):

		for addr in self.peers:
			print addr

		message = raw_input("Message: ")

		for addr in self.peers:

			ssnd = self.peers[addr]

			try:
				ssnd.sendall(message)
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
	port = 6000

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