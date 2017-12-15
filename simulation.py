import psycopg2, sys, json, csv
from os import path
from peer import Peer

try:
	conn = psycopg2.connect("dbname=sample user=postgres password=toor port=10000")
except:
	print "Cannot connect to database"
	sys.exit()

cur = conn.cursor()
ip_addr = '127.0.0.1'
port = 6000
myself = Peer(ip_addr, port, True)

print "Connecting to peer..."
ip_addr = raw_input("IP Address: ")
port = input("Port: ")
myself.getPeers([(ip_addr, port)])

sender = raw_input("Sender: ")
receiver = raw_input("Receiver: ")
transaction = raw_input("Path: ")

cur.execute("CREATE TABLE sample (id serial PRIMARY KEY, sender varchar, receiver varchar, data varchar);")

with open(transaction, 'rb') as csvfile:
	finput = csv.reader(csvfile)
	fname = path.basename(csvfile.name)

	parameters = next(finput)
	paramsize = len(parameters)

	for values in finput:
		data = {}

		for i in range(0, paramsize):
			data[str(parameters[i])] = str(values[i])

		data = json.dumps(data)	

		cur.execute("INSERT INTO sample(sender, receiver, data) VALUES (%s, %s, %s)", 
			(sender, receiver, data))
		print "Inserted to database:", values
		myself.sendMessage(ip_addr, port, data, 1)


cur.execute("DROP TABLE sample;")

conn.commit()
cur.close()

try:
	conn.close()
	print "End Process"
except:
	print "Cannot close connection"
	sys.exit()
