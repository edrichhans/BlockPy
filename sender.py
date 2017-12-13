import py2p

def connect(ipaddr = None, port = None, id = None):
	sock = py2p.MeshSocket('0.0.0.0', 4445)

	ipaddr = raw_input('Input IP Address of server: ') if not ipaddr else ipaddr
	port = input('Input Port: ') if not port else port

	sock.connect(ipaddr, port, id)

	return sock

def sender(sock, msg = None):
	msg = raw_input('Message: ') if not msg else msg

	if msg != '':
		sock.send(msg)
	return msg

def disconnect(sock, id = None):
	sock.disconnect(id)

if __name__ == '__main__':
	sock = connect()
	while sender(sock):
		continue