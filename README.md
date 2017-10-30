# BlockPy

BlockPy is an attempt to create a python API for a blockchain-based data integrity verifier.

Currently uses py2p for its meshSocket at port 4444.

## Files

These will describe specific files and their functionalities.

### main.py

Main.py is a sample server file

The following are the functionalities in order.

* Connect to meshSocket using port 4444
* Read chain from JSON/sampleblock.json
* Wait for transaction
* Create block from transaction
* Append block to chain
* Persist chain to JSON/sampleblock.json
* Loop

### sender.py

Sample client file. It accepts IP address and port of server file, and a JSON raw_input to send to a running main.py

### chain.py

Reads, writes and view the chain.

### block.py

Formats transactions and blocks.

### checking.py

Checks for validity of chain, block, hashes.

### hashMe.py

sha256 hashing. hashMe() works with JSON and text formats.

## Things to do

* ~~Migrate from sockets to a better p2p library (py2p or pyp2p)~~
* Broadcast instead of single point
* Make this into an API
* Add better validations