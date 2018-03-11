# BlockPy
BlockPy is an attempt to create a python API for a blockchain-based data integrity verifier.

Currently uses python native sockets

## Setup

### Create `database.ini`

Contents:
```
[postgresql]
host=localhost
database=blockpy
user=postgres
password=toor
port=10000
```
Set the port to `5432` for default postgre port.

## Commands

### `send`
Send a JSON message to a specific machine using IP address and port. 

### `broadcast message`
Broadcasts a message to all connected peers

### `disconnect`
Disconnects from the blockchain network

### `verify`
Verify a transaction given its number using the blockchain.

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

## How integrity verification works
The network implements a Merkle Root when generating a block. The merkle root is used to verify a transaction by getting and hashing together all other transactions within the same block in a manner used to generate the merkle root. The generated merkle root is then compared to the existing one from the queried block.

## Things to do
Catch errors, implement timeout schemes, code cleanup, comparison with other integrity verification softwares, change miner scheme

