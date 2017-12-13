# BlockPy

BlockPy is an attempt to create a python API for a blockchain-based data integrity verifier.

Currently uses python native sockets

## Files

These will describe specific files and their functionalities.

### Main.py

Main.py contains functions of the main blockchain

The following are the functionalities

* Connect to PostgreSQL database
* `username = edrichhans`
* `password = password`
* `create()` accepts a message parameter
* Create block from transaction
* Append block to chain
* Persist chain to database

### peer.py

Sample peer file. connects to other peers in the network and runs `create()` from `main.py`

### sender.py

Sample client file. It accepts IP address and port of server file, and a JSON raw_input to send to a running main.py

### chain.py

Reads, writes and view the chain. Persistence to db is here

### block.py

Formats transactions and blocks.

### checking.py

Checks for validity of chain, block, hashes.

### hashMe.py

sha256 hashing. `hashMe()` works with JSON and text formats.

## Things to do

The bottom part starting from the creation of the `nodeBchain` variable is an example of a node adding its own block to the chain.