run peer.py and peer2.py

both contain the same code, just different default ip and port

you can specify your own ip and port by entering the ff in the terminal: python peer.py -h <ip> -p port

once up and running, go to peer.py and enter "get peers"

then input "ip address port" 
ex: 127.0.0.1 7000

then peer.py can send messages to peer2.py

enter "send message" for command

then enter peer2.py's hostname and port and message

switch to peer2.py terminal

you can see that you've already established a connection beceause of peer.py earlier

so enter "send message" right away and enter peer.py's hostname, port and message

you will the message in peer.py's terminal