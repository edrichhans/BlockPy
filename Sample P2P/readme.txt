run peer.py and server.py

both contain the same code, just different default ip and port

you can specify your own ip and port by entering the ff in the terminal: python peer.py -h <ip> -p port

WARNING: dont change host and port of server.py for now.

once they run, they are already listening for other nodes while waiting for an input command

currently, enter commands only on peer.py

available commands:
get peers - connect to server.py (since server.py is assumed as the community peer that is always available for new peers to connect to and ask for more peers)

send message- prints out your current peer list, then asks you which you would like to connect to. you cannot send a message to an address not in your peer list