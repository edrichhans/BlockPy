import json
from datetime import date
from collections import OrderedDict
from block import makeBlock
from hashMe import hashMe

def readChain(finput):
    chain = []
    try:
        with open (finput, 'r') as f:
            chainJSON = json.load(f, object_pairs_hook=OrderedDict)
        for blockJSON in chainJSON:
            parentHash = blockJSON['contents']['parentHash']
            blockTxn = blockJSON['contents']['blockTxn']
            txnCount = blockJSON['contents']['txnCount']
            blockNumber = blockJSON['contents']['blockNumber']
            timestamp = blockJSON['contents']['timestamp']
            block = {
                'hash': blockJSON['hash'], 
                'contents': {
                    'parentHash': parentHash, 
                    'txnCount': txnCount,
                    'blockTxn': blockTxn, 
                    'blockNumber': blockNumber,
                    'timestamp': timestamp
                    #'digital signature': 
                    }
                }
            chain.append(block)

        return chain
    except:
        with open(finput, 'w') as f:
            genesisBlockContents = {
                'blockNumber':0,
                'parentHash':None,
                'txnCount':0,
                'blockTxn':None,
                'timestamp': str(date.today())
            }
            genesisHash = hashMe(genesisBlockContents)
            genesisBlock = {
                'hash':genesisHash,
                'contents':genesisBlockContents
            }
            chain = [genesisBlock]
            return chain


def viewChain(chain):
    for block in chain:
        blockHash = block['hash']
        hashLen = len(blockHash)
        blockTxn = block['contents']['blockTxn']
        blockNumberFormatted = '| BlockNumber: ' + str(block['contents']['blockNumber'])
        print ('=' * (hashLen+4))
        print blockNumberFormatted + ' ' * (hashLen - len(blockNumberFormatted) + 2) + ' |'
        print ('=' * (hashLen+4))
        print '|' + ' ' * ((hashLen/2)-1) + 'hash' + ' ' * ((hashLen/2)-1) + '|'
        print '| ' + block['hash'] + ' |'
        print '|' + ' ' * (hashLen+2) + '|'
        print '|' + ' ' * ((hashLen/2)-3) + 'blockTxn' + ' ' * ((hashLen/2)-3) + '|'
        print '| ' + (blockTxn if blockTxn != None else ' ' * ((hashLen/2)-2) + 'NULL' + ' ' * ((hashLen/2)-2)) + ' |'
        print ('=' * (hashLen+4))
        print (' ' * (hashLen/2)) + '  |'

def writeChain(chain, foutput):
    with open(foutput,'w') as foutput:
        json.dump(chain, foutput, indent=4)