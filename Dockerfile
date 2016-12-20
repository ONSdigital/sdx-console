FROM onsdigital/flask-crypto-queue

ADD console /app/console
ADD server.py /app/server.py
ADD requirements.txt /app/requirements.txt
ADD startup.sh /app/startup.sh

# set working directory to /app/
WORKDIR /app/

EXPOSE 5000
EXPOSE 15678

RUN pip3 install --no-cache-dir -U -I -r /app/requirements.txt

ENTRYPOINT ./startup.sh
