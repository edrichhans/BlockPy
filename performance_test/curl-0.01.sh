sleep 0.1s
curl http://localhost:5002/insert -d 'content=asdf' -X POST -v --retry 10
sleep 0.1s
curl http://localhost:5002/insert -d 'content=a' -X POST -v --retry 10
sleep 0.1s
curl http://localhost:5002/insert -d 'content=sdf' -X POST -v --retry 10
sleep 0.1s
curl http://localhost:5002/insert -d 'content=df' -X POST -v --retry 10
sleep 0.1s
curl http://localhost:5002/insert -d 'content=f' -X POST -v --retry 10