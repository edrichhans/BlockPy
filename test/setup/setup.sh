sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo pip install virtualenv
virtualenv --version
virtualenv ../venv
source ../venv/bin/activate
sudo pip install -r pip-requirements.txt
cat > ../database.ini <<- "EOF"
[postgresql]
host=localhost
database=blockpy
user=postgres
password=toor
port=5432
EOF
