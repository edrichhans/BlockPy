sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo pip install virtualenv
virtualenv --version
virtualenv ../venv
source ../venv/bin/activate
sudo pip install -r requirements-pip.txt
sudo -u postgres psql postgres -t "SELECT 1 FROM blockpy WHERE datname='blockpy'" | grep -q 1 || sudo -u postges psql postgres -c "CREATE DATABASE blockpy"
cat > ../database.ini <<- "EOF"
[postgresql]
host=localhost
database=blockpy
user=postgres
password=toor
port=5432
EOF
