import json, socket, sys, getopt, select
from threading import Thread

class PeerListen(Thread):

	def __init__(self, ip_addr, port):

		Thread.__init__(self)
		self.peers = []
		self.ip_addr = ip_addr
		self.port = port

		#socket for receiving messages
		self.srcv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.srcv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		print "hostname", self.ip_addr
		print "port", self.port
		self.srcv.bind((self.ip_addr, self.port))
		#add self to list of peers
		self.peers.append(self.srcv)

		#listen up to 5 other peers
		self.srcv.listen(5)

	def __del__(self):
		self.srcv.close()

	def run(self):

		while True:

			read_sockets,write_sockets,error_sockets = select.select(self.peers,[],[])
			for socket in read_sockets:

				if socket == self.srcv:
					#try:
					conn, addr = self.srcv.accept()
					self.peers.append(conn)
					print "\nEstablished connection with: ", addr
					#except:
						#print "\nNothing to accept"

				else:
					try:
						message = socket.recv(1024)
						print message
					except Exception as e:
						print "Data err", e
						self.peers.remove(socket)
						continue

class PeerSend(Thread):

	community_ip = ('127.0.0.1', 5000)

	def __init__(self, ip_addr, port):

		Thread.__init__(self)
		self.peers = []
		self.ip_addr = ip_addr
		self.port = port
		self.ssnd = None

		print "hostname", self.ip_addr
		print "port", self.port


	# def __del__(self):
	# 	self.ssnd.close()
	
	def run(self):
		while True:
			command = raw_input("Enter command: ")

			if command == "get peers":
				self.getPeers()
			elif command == "send message":
				self.send()
			else:
				print "Unknown command"

	def getPeers(self, peer_addr = []):

		#socket for receiving messages
		ssnd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		ssnd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		ssnd.bind((self.ip_addr, self.port))

		if len(self.peers) == 0:
			try:
				ssnd.connect(self.community_ip)
				self.peers.append(self.community_ip)
				print "Connected: ", self.community_ip[0], self.community_ip[1]
				ssnd.close()
			except:
				print "Community server down"
				ssnd.close()

		else:
			for addr in peer_addr:
				self.peers.append(addr)
				print "Connected: ", addr[0], addr[1]			

	def send(self):

		for peers in self.peers:
			print peers

		ip = raw_input("IP Address: ")
		port = input("Port: ")

		if (ip, port) in self.peers:

			message = raw_input("Message: ")
			#socket for receiving messages
			ssnd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			ssnd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			ssnd.bind((self.ip_addr, self.port))

			try:
				ssnd.connect((ip, port))
				ssnd.sendall(message)
				ssnd.close()
			except Exception as e:
				ssnd.close()
				print e

		else:
			print "Peer not recognized"

#main code to run when running peer.py
#include in your input the hostname and the port you want your peer to run in
#example: python peer.py -h 127.0.0.1 -p 6000
#if no arguments passed, will use the default ip and port
def main(argv):
	#this is the default ip and port
	ip_addr = '127.0.0.1'
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
	#for now, this code can only send messages or get new peers
	#while sender.py only listens for new peers to connect to
	#or new messages to read from existing peers
	receiver = PeerListen(ip_addr, port)
	receiver.start()

	sender = PeerSend(ip_addr, port+1)
	sender.start()
		

#IGNORE CODE BELOW!!!
#-------------------------------------------------------------------------------
# from flask import Flask, redirect, url_for, request, render_template, Response
# import json

# node = Flask(__name__)

# txns = []
# peers = []

# @node.route('/')
# def index():
# 	return "Blockchain Flask p2p"

# @node.route('/receiveTxn', methods=['POST', 'GET'])
# def receiveTxn():
# 	#if request.method == 'POST':

# 	jsondata = request.get_json()
# 	data = json.loads(jsondata)
	
# 	senderKey = data['senderKey']
# 	receiverKey = data['receiverKey']
# 	txn = data['txn']
# 	txns.append([str(senderKey), str(receiverKey), str(txn)])
# 	return str(txns)

# @node.route('/view')
# def viewTxns():

# 	return str(txns)

# @node.route('/getPeers')
# def retPeers():
# 	return peers

# @node.route('/requestTxn', methods=['POST', 'GET'])
# def requestTxn():
# 	if len(txns) > 0:
# 		returnTxn = txns[0]
# 		resp = Response(json.dumps(returnTxn), status=200, mimetype='application/json')
# 		print resp.get_data()
# 		return resp
# 	return Response(None, status=400)

# if __name__=='__main__':
# 	peers.append(['127.0.0.1', 5002])
# 	node.run('127.0.0.1',5000,True)