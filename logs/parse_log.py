import json
from datetime import datetime

DIR = './'

peer = open(DIR + 'peer.log')
print '='*30, 'PEER', '='*30

for line in peer:
    log = json.loads(line)
    if 'message' in log.keys():
        message = log['message']
        time = datetime.strptime(log['asctime'], '%Y-%m-%dT%H:%M:%SZ+%f')
        if message == 'Sending transaction':
            print 'Sending to miners:\t', time, '\t', log['contents']
        elif message == 'Block generated':
            print 'Block generated:\t', time, '\t', log['blockHash'][:10] + '...'
        elif message == 'Signed block sent':
            print 'Signed block sent:\t', time, '\t', log['blockHash'][:10] + '...'

peer.close()

communityPeer = open(DIR + 'community-peer.log')
print '='*30, 'COMMUNITY', '='*30

for line in communityPeer:
    log = json.loads(line)
    if 'message' in log.keys():
        time = datetime.strptime(log['asctime'], '%Y-%m-%dT%H:%M:%SZ+%f')
        if log['message'] == 'Block signature verified':
            print 'Sig Verified:\t', time, '\t', log['hash'][:10] + '...'
        elif log['message'] == 'Broadcasted chain and txns':
            print 'Broadcasted:\t', time
        elif log['message'] == 'Current miner updated':
            print 'Updated Miner:\t', time, '\t', log['miner']
        elif log['message'] == 'Updated tables':
            print 'Updated tables:\t', time, '\tBlock #', log['blockNumber']
        elif log['message'] == 'Block returned for verification':
            print 'Returned Block:\t', time

communityPeer.close()
