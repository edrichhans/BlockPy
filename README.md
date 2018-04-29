# BlockPy
BlockPy is an attempt to create a python API for a blockchain-based data integrity verifier.

Currently uses python native sockets

## Setup

### For Unix
#### `cd` to `/setup` and run `bash setup.sh`.

#### Change user `postgres` password to `toor`
* `sudo -u postgres psql postgres`
* `\password postgres`
* `toor`
* `\q`

### Create `database.ini`

Contents:
```
[postgresql]
host=localhost
database=blockpy
user=postgres
password=toor
port=5432
```
Set the port to `5432` for default postgre port.

## API
Run `python webapp.py`, which calls a `Peer` instance from `peer.py`.
The server runs on http://localhost:5002

### `GET /txns`
Returns the list of transactions as a JSON object.

### `GET /txns/<id>`
Returns the transaction at the specified id (txn_number) as a JSON object.

### `GET /blocks`
Returns the list of blocks in the blockchain as a JSON object.

### `GET /blocks/<id>`
Returns the block at the specified id (block_number) as a JSON object.

### `POST /verify`
Verifies the transaction given the txn number using the `txn` parameter.
Returns `true` if verified, else returns `false`.
* Example: `curl http://localhost:5002/verify -d "txn=1" -X POST -v`

### `POST /insert`
Inserts a transaction given the content using the `content` parameter.
Returns `true` if verified, else returns `false`.
* Example: `curl http://localhost:5002/insert -d "content=<transaction contents here>" -X POST -v`

## Sample GUI
To run the sample GUI:
* Run `python webapp.py` to run API server.
* Run `python -m SimpleHTTPServer 8080` in the `/views` directory.
* Open `localhost:8080` in browser.

Note: Browser's Cross-Origin Restrictions must be disabled for this to work.


## Commands
These are the commands accepted by `raw_input` if `peer.py` is run from the terminal.

### `default`
Send a message to the set miner(s) as a transaction. 

### `send`
Send a message to a specific machine using IP address and port as a transaction. 

### `broadcast message`
Broadcasts a message to all connected peers

### `disconnect`
Disconnects from the blockchain network

### `verify`
Verify a transaction given its number using the blockchain.

### `create user`
Create new credentials for a peer instance.

### `reset users`
Drop users table.

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

### login.py
Handles `peer.py` login authentication at `community_peer.py`. Credentials are sent from `peer.py` to `community_peer.py` where they are verified, if valid authorization message is sent to peer.py which will then allow the process to send the public key list found in `community_peer.py`

### webapp.py
Runs the API Server.

## How integrity verification works
The network implements a Merkle Root when generating a block. The merkle root is used to verify a transaction by getting and hashing together all other transactions within the same block in a manner used to generate the merkle root. The generated merkle root is then compared to the existing one from the queried block.

## Things to do
Catch errors, implement timeout schemes, code cleanup, comparison with other integrity verification softwares, change miner scheme

