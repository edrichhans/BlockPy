from flask import Flask, redirect, url_for, request, render_template
import json

node = Flask(__name__)

txns = []

@node.route('/')
def index():
	return "Blockchain Flask p2p"
	
@node.route('/receive', methods=['POST', 'GET'])
def receiveTxn():
	#if request.method == 'POST':

	jsondata = request.get_json()
	data = json.loads(jsondata)
	
	senderKey = data['senderKey']
	receiverKey = data['receiverKey']
	txn = data['txn']
	txns.append([str(senderKey), str(receiverKey), str(txn)])
	print txns
	return str(txns)

@node.route('/view')
def viewTxns():

	return str(txns)

if __name__=='__main__':
	node.run('127.0.0.1',5000,True)