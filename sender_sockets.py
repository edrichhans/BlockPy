import logging
from socketIO_client import SocketIO, LoggingNamespace

logging.getLogger('requests').setLevel(logging.WARNING)
logging.basicConfig(level=logging.DEBUG)

def send(ip, port, message):
	with SocketIO(ip, port, LoggingNamespace) as socketIO:
	    socketIO.emit('message', message)
	    socketIO.wait(seconds=1)

if __name__ == '__main__':
	ip = raw_input("IP: ")
	port = input("port: ")
	message = raw_input("Message: ")

