# BlockPy

BlockPy is an attempt to create a python API for a blockchain-based data integrity verifier.

Currently uses sockets for client-server connections. Will migrate to a better p2p library.

## Files

These will describe specific files and their functionalities.

### main.py

Main.py is a sample server file

The following are the functionalities in order.

* Open localhost socket at port 9999
* Read chain from JSON/sampleblock.json
* Wait for connection
* Once connected, wait for transaction
* Create block from transaction
* Append block to chain
* Persist chain to JSON/sampleblock.json

### sender.py

Sample client file. It accepts a JSON raw_input and sends it to a running main.py (localhost, port 9999)

### chain.py

Reads, writes and view the chain.

### block.py

Formats transactions and blocks.

### checking.py

Checks for validity of chain, block, hashes.

### hashMe.py

sha256 hashing. hashMe() works with JSON and text formats.

## Things to do

* Migrate from sockets to a better p2p library (py2p or pyp2p)
* Broadcast instead of single point
* Make this into an API
* Add better validations