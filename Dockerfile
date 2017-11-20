FROM onsdigital/flask-crypto-queue

COPY console /app/console
COPY requirements.txt /app/requirements.txt
COPY server.py /app/server.py
COPY startup.sh /app/startup.sh
COPY Makefile /app/Makefile

# set working directory to /app/
WORKDIR /app/

EXPOSE 4200

RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get install -yq git gcc make build-essential python3-dev python3-reportlab
RUN make build

ENTRYPOINT ./startup.sh

ENV DEVELOPMENT_MODE True
