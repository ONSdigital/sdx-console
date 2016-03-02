FROM python:3.5

ADD requirements.txt /app/requirements.txt
ADD server.py /app/server.py

# set working directory to /app/
WORKDIR /app/

# install python dependencies
RUN pip install -r requirements.txt

EXPOSE 5000

ENTRYPOINT python server.py