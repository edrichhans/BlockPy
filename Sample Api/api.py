from flask import Flask, redirect, url_for, request, render_template

node = Flask(__name__)

txns = []

@node.route('/')
def index():
	return render_template('login.html')

@node.route('/login',methods = ['POST', 'GET'])
def login():
   del txns[:]
   if request.method == 'POST':
      user = request.form['nm']
   else:
      user = request.args.get('nm')
   return redirect(url_for('account', name=user))

@node.route('/transaction',methods = ['POST', 'GET'])
def transaction():
   if request.method == 'POST':
      txn = request.form['txn']
      user = request.form['user']
   else:
      txn = request.args.get('txn')
      user = request.args.get('user')

   if txn != '':
   	  txns.append(txn)

   return redirect(url_for('account', name=user))


@node.route('/account/<name>')
def account(name):
	return render_template('send_txn.html', user=name, txns = txns)


if __name__=='__main__':
	node.run('0.0.0.0',5000,True)