import socket
import sys

s = socket.socket()
s.connect(("localhost",9999))

while True:
	data = raw_input("Enter data:")
	if data == 'q':
		s.send('')
		break
	s.send(data)
print "Done Sending"
s.shutdown(socket.SHUT_WR)
print s.recv(1024)
s.close()