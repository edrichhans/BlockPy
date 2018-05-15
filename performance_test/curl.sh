sleep $((RANDOM %10))
curl http://localhost:5002/insert -d 'content=a' -v --retry 10
sleep $((RANDOM %10))
curl http://localhost:5002/insert -d 'content=b' -v --retry 10
sleep $((RANDOM %10))
curl http://localhost:5002/insert -d 'content=c' -v --retry 10
sleep $((RANDOM %10))
curl http://localhost:5002/insert -d 'content=d' -v --retry 10
sleep $((RANDOM %10))
curl http://localhost:5002/insert -d 'content=e' -v --retry 10
sleep $((RANDOM %10))
curl http://localhost:5002/insert -d 'content=f' -v --retry 10
sleep $((RANDOM %10))
curl http://localhost:5002/insert -d 'content=g' -v --retry 10
sleep $((RANDOM %10))
curl http://localhost:5002/insert -d 'content=h' -v --retry 10
sleep $((RANDOM %10))
curl http://localhost:5002/insert -d 'content=i' -v --retry 10
sleep $((RANDOM %10))
curl http://localhost:5002/insert -d 'content=j' -v --retry 10
sleep $((RANDOM %10))
curl http://localhost:5002/insert -d 'content=k' -v --retry 10
sleep $((RANDOM %10))
curl http://localhost:5002/insert -d 'content=l' -v --retry 10
sleep $((RANDOM %10))
curl http://localhost:5002/insert -d 'content=m' -v --retry 10
sleep $((RANDOM %10))
curl http://localhost:5002/insert -d 'content=n' -v --retry 10
sleep $((RANDOM %10))
curl http://localhost:5002/insert -d 'content=o' -v --retry 10
