import psycopg2, sys, json, csv, datetime, unicodedata
from config import config
from peer import Peer
from flask import Flask, request
from flask_restful import Resource, Api, reqparse
from flask.ext.jsonpify import jsonify

params = config()
conn = psycopg2.connect(**params)
cur = conn.cursor()

ip_addr = '127.0.0.1'
port = 3000
myself = Peer(ip_addr, port, False)

app = Flask(__name__)
api = Api(app)

parser = reqparse.RequestParser()
parser.add_argument('txn')
parser.add_argument('content')

def myconverter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()

class Txns(Resource):
    def get(self):
        query = 'SELECT * FROM txns;'
        cur.execute(query)
        keys = [desc[0] for desc in cur.description]
        txns = cur.fetchall()
        if txns:
            result = {"txns": [dict(zip(keys, json.loads(json.dumps(i, default=myconverter)))) for i in txns]}
        else:
            result = {}
        return jsonify(result)

class Txns_id(Resource):
    def get(self, id):
        query = 'SELECT * FROM txns WHERE txn_number = %s;' %int(id)
        cur.execute(query)
        keys = [desc[0] for desc in cur.description]
        txn = cur.fetchone()
        if txn:
            result = dict(zip(keys, json.loads(json.dumps(txn, default=myconverter))))
        else:
            result = {}
        return jsonify(result)

class Blocks(Resource):
    def get(self):
        query = 'SELECT * FROM blocks;'
        cur.execute(query)
        keys = [desc[0] for desc in cur.description]
        blocks = cur.fetchall()
        if blocks:
            result = {"chain": [dict(zip(keys, json.loads(json.dumps(i, default=myconverter)))) for i in blocks]}
        else: 
            result = {}
        return jsonify(result)

class Blocks_id(Resource):
    def get(self, id):
        query = 'SELECT * FROM blocks WHERE block_number = %s;' %int(id)
        cur.execute(query)
        keys = [desc[0] for desc in cur.description]
        block = cur.fetchone()
        if block:
            result = dict(zip(keys, json.loads(json.dumps(block, default=myconverter))))
        else:
            result = {}
        return jsonify(result)

class Verify(Resource):
    def post(self):
        args = parser.parse_args()
        txn = args['txn']
        return myself.getTxn(txn)

class Insert(Resource):
    def post(self):
        args = parser.parse_args()
        content = args['content']
        content = unicodedata.normalize('NFKD', content).encode('ascii','ignore')
        print content
        return myself.sendToMiners('dummy', content)

class GetPeers(Resource):
    def get(self):
        return jsonify(myself.getPeersAPI())

api.add_resource(Txns, '/txns')
api.add_resource(Txns_id, '/txns/<id>')
api.add_resource(Blocks, '/blocks')
api.add_resource(Blocks_id, '/blocks/<id>')
api.add_resource(Verify, '/verify')
api.add_resource(Insert, '/insert')
api.add_resource(GetPeers, '/peers')


if __name__ == '__main__':
    app.run(port='5002')