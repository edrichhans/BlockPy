import subprocess
import os

process = subprocess.Popen(['hostname','-I'], stdout = subprocess.PIPE)
ip_addr = process.communicate()[0]
print ip_addr.split()[0]

firstString = "python webapp.py -h " 
secondString = " -p 8000 --community_ip=10.147.72.32 --community_port=5000 --username=user --password=user"
finalCommand = firstString + ip_addr.split()[0] + secondString
print finalCommand

os.system(finalCommand)