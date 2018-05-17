sleep 0.5s
curl http://localhost:5002/insert -d 'content=a' -v --retry 10
sleep 0.5s
curl http://localhost:5002/insert -d 'content=b' -v --retry 10
sleep 0.5s
curl http://localhost:5002/insert -d 'content=c' -v --retry 10
sleep 0.5s
curl http://localhost:5002/insert -d 'content=d' -v --retry 10
sleep 0.5s
curl http://localhost:5002/insert -d 'content=e' -v --retry 10