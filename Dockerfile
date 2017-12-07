FROM onsdigital/flask-crypto-queue

COPY console /app/console
COPY requirements.txt /app/requirements.txt
COPY server.py /app/server.py
COPY startup.sh /app/startup.sh
COPY Makefile /app/Makefile

# set working directory to /app/
WORKDIR /app/

EXPOSE 4200

RUN make build

ENTRYPOINT ./startup.sh

ENV DEVELOPMENT_MODE True
