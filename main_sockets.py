#!flask/bin/python
from __future__ import print_function
from flask import Flask, request, jsonify
from flask_socketio import SocketIO
import time, json
from sys import argv, exit
from block import makeBlock, makeTxn
from checking import checkChain, checkBlockValidity
from hashMe import hashMe
from chain import readChain, viewChain, writeChain

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

maxTxns = 1
blockLocation = 'JSON/Chain.json'

@socketio.on('message')
def handle_message(message):
    print('received message: ' + message)

    txnList = []
    msg = message
    if (msg and msg.packets[1:]):
        print(msg)
        packet = msg.packets[1]
        try:
            txn = json.loads(packet)
        except:
            txn = packet
        txn['content'] = hashMe(json.dumps(txn['content']))
        txnList.append(makeTxn(txn['_owner'], txn['_recipient'], txn['content']))
        print('Done Receiving\n')
        newBlock = makeBlock(txnList, chain)
        checkBlockValidity(newBlock, chain[-1])
        chain.append(newBlock)
        checkChain(chain)
        viewChain(chain)
        print('Writing to file...\n')
        writeChain(chain, blockLocation)


if __name__ == '__main__':
    print('\nReading contents of current chain...\n')
    chain = readChain(blockLocation)
    viewChain(chain)

    socketio.run(app)