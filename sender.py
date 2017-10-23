import socket
import sys
import json

s = socket.socket()
s.connect(("localhost",9999))

while True:
	data = raw_input("Enter data:")
	if data == 'q':
		s.send('')
		break
	try:
		json.loads(data)
		s.send(data)
	except:
		print "Invalid JSON"

print "Done Sending"
s.shutdown(socket.SHUT_WR)
print s.recv(1024)
s.close()