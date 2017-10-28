import py2p

sock = py2p.MeshSocket('0.0.0.0', 4444)

ipaddr = raw_input('Input IP Address of server: ')
port = input('Input Port: ')

sock.connect(ipaddr, port)

while True:
	msg = raw_input('Message: ')
	sock.send(msg)
