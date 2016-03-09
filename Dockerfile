FROM iwootten/flask-crypto

ADD requirements.txt /app/requirements.txt
ADD server.py /app/server.py
ADD static /app/static
ADD templates /app/templates

# set working directory to /app/
WORKDIR /app/

# install python dependencies
RUN pip install -r requirements.txt

EXPOSE 5000

ENTRYPOINT python server.py