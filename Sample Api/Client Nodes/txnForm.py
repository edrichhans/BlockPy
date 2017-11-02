from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, SubmitField, TextAreaField

class SendTxnForm(FlaskForm):
	senderKey = PasswordField('Sender Private Key')
	receiverKey = StringField('Receiver Public Key')
	txn = TextAreaField('Transaction')
	submit = SubmitField("Send")

