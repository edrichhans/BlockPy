import peer
import subprocess
import os
import sys
import time


MAX_MESSAGES = 40
SIM = True
def mock_test_credentials():
    return "test"
def mock_getAuth():
# Perform Login using given credentials
    import login
    login.raw_input = mock_test_credentials
    login.getpass.getpass = mock_test_credentials

def init_Peer():
#Get main IP Address assign to computer on the LAN - presumambly works on 
#all linux devices
    mock_getAuth()
    process = subprocess.Popen(['hostname','-I'], stdout = subprocess.PIPE)
    ip_addr = process.communicate()[0]
    port = 6000 #default, since we won't be running locally
    newPeer = peer.Peer(ip_addr, port, SIM)
    return newPeer

thisNode = init_Peer()
thisNode.sthread.start()
#wait for miners to be set
count = 0
time.sleep(3)

if thisNode.miners:

    while count < MAX_MESSAGES:
        if not thisNode.lockSending:
            thisNode.sendToMiners('dummy', 'test')
            print("MESSAGE SENT")
            thisNode.lockSending = True
            count = count + 1
# Start sequential sending