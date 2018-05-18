import peer
import peer1
import peer2
import peer3
import peer4
import peer5
import peer6
import community_peer
import thread
import time

blockTotal = 1
delay = 0.1

comm = community_peer.Community_Peer(sim=True) 	
threads = [peer.Peer(sim=True),
	peer1.Peer(sim=True),
	peer2.Peer(sim=True),
	peer3.Peer(sim=True),
	peer4.Peer(sim=True),
	peer5.Peer(sim=True),
	peer6.Peer(sim=True)]

while 1:
	for athread in threads:
		athread.sendToMiners("dummy",str(blockTotal))
		time.sleep(delay)
	blockTotal += 1
	if blockTotal > 10:
		x=0
		for athread in threads:
			athread.endPeer()
			print "Peer ",x," End"
			x += 1
		comm.endPeer()
		print "Comm End"
		break