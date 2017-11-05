from flask import Flask, redirect, url_for, request, render_template
from txnForm import SendTxnForm
from acctLogin import *
import json
import requests

node = Flask(__name__)
node.secret_key = 'chinesesecuritygroup'
#login_manager.init_app(node)

txns = []
peers = []

@node.route('/')
def index():
	#return render_template('login.html')
	form = SendTxnForm()

	return render_template('sendTxn.html', form = form)

@node.route('/sendTxn')
def sendTxn():
	form = SendTxnForm()

	return render_template('sendTxn.html', form = form)

@node.route('/receiveForm', methods=['POST', 'GET'])
def receive():

	if request.method == 'POST':
		peerAddr = request.form['peerAddr']
		peers.append(peerAddr)
		senderKey = request.form['senderKey']
		receiverKey = request.form['receiverKey']
		txn = request.form['txn']

	finaltxn = {'senderKey': senderKey, 
		'receiverKey': receiverKey, 
		'txn': txn}
	finaltxn = json.dumps(finaltxn)

	if str(''.join(peerAddr[0:7])) == 'http://':
		requests.post(str(peerAddr)+"/receiveTxn", json = finaltxn)
	else:
		requests.post("http://"+str(peerAddr)+"/receiveTxn", json = finaltxn)

	return redirect(url_for('sendTxn'))

@node.route('/receiveTxn', methods=['POST', 'GET'])
def receiveTxn():
	if request.method == 'POST':

		jsondata = request.get_json()
		data = json.loads(jsondata)
		
		senderKey = data['senderKey']
		receiverKey = data['receiverKey']
		txn = data['txn']
		txns.append([str(senderKey), str(receiverKey), str(txn)])
		
	return str(txns)

@node.route('/view')
def viewTxns():
	return str(txns)

if __name__=='__main__':
	peers.append(['127.0.0.1', 5003])
	node.run('127.0.0.1',5002,True)