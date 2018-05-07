sudo -H pip install virtualenv
virtualenv --version
sudo -H virtualenv ../venv
source ../venv/bin/activate
sudo -H pip install -r /home/BlockPy/setup/requirements-pip.txt
sudo bash -c 'cat > /home/BlockPy/database.ini <<- "EOF"
[postgresql]
host=localhost
database=blockpy
user=postgres
password=toor
port=5432
EOF'

