from flask import Flask, redirect, url_for, request, render_template
from txnForm import SendTxnForm
from acctLogin import *
import json
import requests

node = Flask(__name__)
node.secret_key = 'chinesesecuritygroup'
#login_manager.init_app(node)

txns = []

@node.route('/')
def index():
	#return render_template('login.html')
	form = SendTxnForm()

	return render_template('sendTxn.html', form = form)

@node.route('/sendTxn')
def sendTxn():
	form = SendTxnForm()

	return render_template('sendTxn.html', form = form)

@node.route('/receive', methods=['POST', 'GET'])
def receive():

	if request.method == 'POST':
		senderKey = request.form['senderKey']
		receiverKey = request.form['receiverKey']
		txn = request.form['txn']

	finaltxn = {'senderKey': senderKey, 
		'receiverKey': receiverKey, 
		'txn': txn}
	finaltxn = json.dumps(finaltxn)
	print finaltxn	
	requests.post('http://127.0.0.1:5000/receive', json = finaltxn)
	return redirect(url_for('sendTxn'))

if __name__=='__main__':
	node.run('127.0.0.1',5003,True)