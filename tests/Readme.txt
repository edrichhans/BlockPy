Open the tests and check if all the values under the comment "#change this" matches your values in the database (community peer and peer credentials, blockchain values, transaction table values). You may  also modify the dummy content of these values to test its validity or add more examples of your own.

To run the tests:
type in terminal: python -m unittest discover -s tests


Values that needs/can be changed:

test2.py
def mock_ask_for_username()

def mock_getpass()

def mock_ask_for_peer_username()

def mock_peer_getpass()

mockpeer = peer.Peer('127.0.0.1',8000,True)

mockpeer = peer.Peer('127.0.0.1',8000,True)

test3.py
def mock_ask_for_username()

def mock_getpass()

def mock_getpeername()

mockpeer = peer.Peer('127.0.0.1',8000,True)

mockpeer = peer.Peer('127.0.0.1',8000,True)

correctpacket = {"_category":"4",
"content":[mockpeer.ip_addr,mockpeer.port,mockpeer.pubkey.encode(HexEncoder)],
"_owner": mockpeer.pubkey.encode(HexEncoder),
"_recipient": None}

peer_addr=[('127.0.0.1','1'),('127.0.0.1','2'),('127.0.0.1','3'),('127.0.0.1','4')]

correctpacket = {"_category":"7",
"content":[mockpeer.ip_addr,mockpeer.port,mockpeer.pubkey.encode(HexEncoder)],
"_owner": mockpeer.pubkey.encode(HexEncoder),
"_recipient": None}

test4.py
content = "Hi"

recpubkey = "dummy"

correctpacket = {'_owner': mockpeer.pubkey.encode(HexEncoder),
'_recipient': recpubkey,
'_category': "1",
'content': mockpeer.privkey.sign(str(hashMe(content))).encode('base64')}

mockpeer = peer.Peer('127.0.0.1',8000,True)

mockpeer.miners = [('127.0.0.1',1),('127.0.0.1',2),('127.0.0.1',3),('127.0.0.1',4)]

mockpeer.port_equiv = {
('127.0.0.1',11):('127.0.0.1',1),
('127.0.0.1',12):('127.0.0.1',2),
('127.0.0.1',3):('127.0.0.1',13),
('127.0.0.1',4):('127.0.0.1',14)}

sentmessages = mockpeer.sendToMiners(recpubkey="samplepubkey",message="sample message")

self.assertIn(address,
[(mockpeer.ip_addr,mockpeer.port),
('127.0.0.1',11),
('127.0.0.1',12),
('127.0.0.1',3),
('127.0.0.1',4)])

mockpeer = peer.Peer('127.0.0.1',8000,True)

mockpeer.max_txns = 3

message = {"_owner": mockpeer.pubkey.encode(HexEncoder),
"_recipient": "dummy",
"_category": "1",
"content": "dummy message"}

mockpeer.port_equiv = {('127.0.0.1',1): ('127.0.0.1',11), ('127.0.0.1',12): ('127.0.0.1',2)}

socket = ("127.0.0.1",1)

socket = ("127.0.0.1",2)

reversesocket = ("127.0.0.1",12)

mockpeer = peer.Peer('127.0.0.1',8000,True)

socket = ('127.0.0.1',1)

packet = {'content':json.dumps("dummy message")}

mockpeer = peer.Peer('127.0.0.1',8000,True)

mockpeer = peer.Peer('127.0.0.1',8000,True)

test5.py
def mock_addToChain(newBlock, conn, cur)

def mock_addToTxns(txn, conn, cur, blockNumber)

def mock_ask_for_username()

def mock_getpass()

def mock_peer_ask_for_username()

def mock_peer_getpass()

newBlock = [		json.dumps({'_owner':mockcom.pubkey.encode(HexEncoder), '_recipient':'dummy recipient', 'content': "dummy content"}),
			json.dumps({'_owner':mockcom.pubkey.encode(HexEncoder), '_recipient':'dummy recipient', 'content': "dummy content"}),
			json.dumps({'_owner':mockcom.pubkey.encode(HexEncoder), '_recipient':'dummy recipient', 'content': "dummy content"}),
			json.dumps({'_owner':mockcom.pubkey.encode(HexEncoder), '_recipient':'dummy recipient', 'content': "dummy content"})
		]

mockcom.received_transaction_from[('127.0.0.1',1)] = mockcom.pubkey.encode(HexEncoder)
		
message = mockcom.privkey.sign(str(hashMe("dummy message"))).encode('base64')
		
peer = ('127.0.0.1',1)

json_message['content'] = [None, None]

json_message['content'][0] = message
		
json_message['content'][1] = hashMe(uuid1().hex)

mockcom.miners = {('127.0.0.1',1),('127.0.0.1',2),('127.0.0.1',3)}
		
mockcom.port_equiv = {
('127.0.0.1',4): ('127.0.0.1',14), 
('127.0.0.1',5): ('127.0.0.1',15),
('127.0.0.1',16): ('127.0.0.1',6)
}

json_message = {}
		
json_message['content'] =  json.dumps({'block': {'blockHash': "dummy hash", 'content': "dummy content"},'txnList': "[]",'contributing': "[('127.0.0.1',4), ('127.0.0.1',5), ('127.0.0.1',6)]"})

json_message['content'] =  json.dumps({'block': {'blockHash': "dummy hash", 'content': "dummy content"},'txnList': "[]",
'contributing': "[('127.0.0.1',4), ('127.0.0.1',5), ('127.0.0.1',6)]"})

json_message['content'] =  json.dumps({'block': {'blockHash': "dummy hash 2", 'content': "dummy content 2"},'txnList': "[]",
'contributing': "[('127.0.0.1',4), ('127.0.0.1',5), ('127.0.0.1',7)]"})

self.assertEqual(json.loads(block[0])['content'], "dummy content")
		
self.assertEqual(json.loads(block[0])['blockHash'], "dummy hash")
