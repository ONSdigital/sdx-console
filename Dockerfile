FROM onsdigital/flask-crypto-queue

ADD encrypter.py /app/encrypter.py
ADD settings.py /app/settings.py
ADD server.py /app/server.py
ADD static /app/static
ADD templates /app/templates
ADD requirements.txt /app/requirements.txt
ADD startup.sh /app/startup.sh

# set working directory to /app/
WORKDIR /app/

RUN mkdir -p /app/static/images

EXPOSE 5000

RUN pip3 install --no-cache-dir -U -I -r /app/requirements.txt

ENTRYPOINT ./startup.sh