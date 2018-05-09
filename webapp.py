import psycopg2, sys, json, csv, datetime, unicodedata, getopt
from config import config
from peer import Peer
from flask import Flask, request
from flask_restful import Resource, Api, reqparse
from flask_jsonpify import jsonify
from blockpy_logging import logger

params = config()
conn = psycopg2.connect(**params)
cur = conn.cursor()
parser = reqparse.RequestParser()
parser.add_argument('txn')
parser.add_argument('content')

def main(argv):
    ip_addr = "127.0.0.1"   # s.getsockname()[0]
    port = 3010
    community_ip = "127.0.0.1"
    community_port = 5000
    sim = False
    username, password = None, None

    try:
        opts, args = getopt.getopt(argv, "h:p:s:ci:cp:user:pass", \
            ["hostname=", "port=", "sim=", "community_ip=", "community_port=", "username=", "password="])
    except Exception as e:
        print "Requires hostname and port number:", e
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--hostname"):
            ip_addr = arg
        elif opt in ("-p", "--port"):
            port = int(arg)
        elif opt in ("-ci", "--community_ip"):
            community_ip = arg
        elif opt in ("-cp", "--community_port"):
            community_port = int(arg)
        elif opt in ("-user", "--username"):
            username = arg
        elif opt in ("-pass", "--password"):
            password = arg
        elif opt in ("-sim", "--sim"):
            if arg == "t":
                sim = True
            else:
                sim = False

    myself = Peer(ip_addr, port, sim, community_ip, community_port, username, password)

    app = Flask(__name__)
    api = Api(app)
    logger.info('API started',
        extra={'addr': ip_addr, 'port':port})

    api.add_resource(Txns, '/txns')
    api.add_resource(Txns_id, '/txns/<id>')
    api.add_resource(Blocks, '/blocks')
    api.add_resource(Blocks_id, '/blocks/<id>')
    api.add_resource(Verify, '/verify')
    api.add_resource(Insert, '/insert')
    api.add_resource(GetPeers, '/peers')

    return app

def myconverter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()

class Txns(Resource):
    def get(self):
        try:
            query = 'SELECT * FROM txns ORDER BY txn_number ASC;'
            cur.execute(query)
            keys = [desc[0] for desc in cur.description]
            txns = cur.fetchall()
            if txns:
                result = {"txns": [dict(zip(keys, json.loads(json.dumps(i, default=myconverter)))) for i in txns]}
            else:
                result = {}
            logger.info('GET /txns')
            return jsonify(result)
        except:
            logger.error('txns table does not exist')
            cur.execute('ROLLBACK')

class Txns_id(Resource):
    def get(self, id):
        try:
            query = 'SELECT * FROM txns WHERE txn_number = %s;' %int(id)
            cur.execute(query)
            keys = [desc[0] for desc in cur.description]
            txn = cur.fetchone()
            if txn:
                result = dict(zip(keys, json.loads(json.dumps(txn, default=myconverter))))
            else:
                result = {}
            logger.info('GET /txns/<id>',
                extra={'txn':result})
            return jsonify(result)
        except:
            logger.error('txns table does not exist')
            cur.execute('ROLLBACK')

class Blocks(Resource):
    def get(self):
        try:
            query = 'SELECT * FROM blocks ORDER BY block_number ASC;'
            cur.execute(query)
            keys = [desc[0] for desc in cur.description]
            blocks = cur.fetchall()
            if blocks:
                result = {"chain": [dict(zip(keys, json.loads(json.dumps(i, default=myconverter)))) for i in blocks]}
            else: 
                result = {}
            logger.info('GET /blocks')
            return jsonify(result)
        except:
            logger.error('blocks table does not exist')
            cur.execute('ROLLBACK')

class Blocks_id(Resource):
    def get(self, id):
        try:
            query = 'SELECT * FROM blocks WHERE block_number = %s;' %int(id)
            cur.execute(query)
            keys = [desc[0] for desc in cur.description]
            block = cur.fetchone()
            if block:
                result = dict(zip(keys, json.loads(json.dumps(block, default=myconverter))))
            else:
                result = {}
            logger.info('GET /blocks/<id>',
                extra={'block': result})
            return jsonify(result)
        except:
            logger.error('blocks table does not exist')
            cur.execute('ROLLBACK')

class Verify(Resource):
    def post(self):
        args = parser.parse_args()
        txn = args['txn']
        isVerified = myself.getTxn(txn)
        logger.info('POST /verify',
            extra={'txn': isVerified})
        return isVerified

class Insert(Resource):
    def post(self):
        args = parser.parse_args()
        content = args['content']
        content = unicodedata.normalize('NFKD', content).encode('ascii','ignore')
        print content
        logger.info('POST /insert',
            extra={'content': content})
        return myself.sendToMiners('dummy', content)

class GetPeers(Resource):
    def get(self):
        logger.info('GET /peers')
        return jsonify(myself.getPeersAPI())

if __name__ == '__main__':
    app = main(sys.argv[1:])
    app.run(port='5002')