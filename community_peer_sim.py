import community_peer
import subprocess
import os
import sys
import time


MAX_MESSAGES = 40
SIM = True
def mock_admin_credentials():
    return "admin"
def mock_user_credentials():
    return "user"
def mock_authAdmin():
# Perform Login using given credentials
    import login
    login.raw_input = mock_admin_credentials
    login.getpass.getpass = mock_admin_credentials

def mock_authUser():
# Perform Login using given credentials
    import login
    login.raw_input = mock_user_credentials
    login.getpass.getpass = mock_user_credentials

def init_Peer():
#Get main IP Address assign to computer on the LAN - presumambly works on 
#all linux devices
    mock_authAdmin()
    process = subprocess.Popen(['hostname','-I'], stdout = subprocess.PIPE)
    ip_addr = process.communicate()[0]
    print ip_addr.split()[0]
    port = 5000 #default, since we won't be running locally
    newPeer = community_peer.Community_Peer(ip_addr.split()[0], port, SIM)
    return newPeer

thisNode = init_Peer()
mock_authUser()
thisNode.resetUsers()
thisNode.createUser()
# thisNode.sthread.start()
# #wait for miners to be set
# count = 0
# time.sleep(3)

# if thisNode.miners:

#     while count < MAX_MESSAGES:
#         if not thisNode.lockSending:
#             thisNode.sendToMiners('dummy', 'test')
#             print("MESSAGE SENT")
#             thisNode.lockSending = True
#             count = count + 1
# # Start sequential sending