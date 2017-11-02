from flask_login import LoginManager, login_user, login_required, logout_user

login_manager = LoginManager()

def getLoginManager():

	return login_manager