import json
from collections import OrderedDict

def readChain(finput):
    with open (finput, 'r') as f:
        chainJSON = json.load(f, object_pairs_hook=OrderedDict)

    chain = []

    for blockJSON in chainJSON:
        parentHash = blockJSON['contents']['parentHash']
        blockTxn = blockJSON['contents']['blockTxn']
        blockNumber = blockJSON['contents']['blockNumber']
        block = {'hash': blockJSON['hash'], 'contents': {'parentHash': parentHash, 'blockTxn': blockTxn, 'blockNumber': blockNumber}}
        chain.append(block)

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