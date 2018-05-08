#Pull official Python image
FROM python:2.7

ENV PYTHONUNBUFFERED=1

#EXPOSE 8000
#Set working directory to /blockpy
WORKDIR /usr/src/app

#Copy requirements to be installed
COPY /setup/requirements-pip.txt requirements-pip.txt
#Run pip install
RUN pip install --upgrade pip && apt-get update && apt-get upgrade -y && apt-get install python-psycopg2 libpq-dev build-essential libssl-dev libffi-dev python-dev python-setuptools -y
RUN pip install -r requirements-pip.txt

#Copy the rest of the blockpy code
COPY . /usr/src/app

CMD [ "python", "./community_peer.py" ]



