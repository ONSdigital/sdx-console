FROM onsdigital/flask-crypto-queue

# set working directory to /app/
WORKDIR /app/

EXPOSE 4200

ENTRYPOINT ./startup.sh

ENV DEVELOPMENT_MODE True

COPY requirements.txt /app/requirements.txt
COPY Makefile /app/Makefile
RUN make build

COPY server.py /app/server.py
COPY startup.sh /app/startup.sh
COPY console /app/console