import hashlib, json, sys
from datetime import datetime

def converter(o):
	if isinstance(o, datetime):
		return o.__str__()

def hashMe(msg=""):
    # For convenience, this is a helper function that wraps our hashing algorithm
    if type(msg)!=str: 
    	print "HASHME", msg
        msg = json.dumps(msg,sort_keys=True, default = converter)  # If we don't sort keys, we can't guarantee repeatability!
        
    if sys.version_info.major == 2:
        return unicode(hashlib.sha256(msg).hexdigest(),'utf-8')
    else:
        return hashlib.sha256(str(msg).encode('utf-8')).hexdigest()

        