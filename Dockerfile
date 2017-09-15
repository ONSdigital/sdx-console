FROM onsdigital/flask-crypto-queue

COPY console /app/console
COPY server.py /app/server.py
COPY requirements.txt /app/requirements.txt
COPY startup.sh /app/startup.sh
COPY Makefile /app/Makefile

# set working directory to /app/
WORKDIR /app/

EXPOSE 5000

RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get install -yq git gcc make build-essential python3-dev python3-reportlab

RUN make build

ENTRYPOINT ./startup.sh
