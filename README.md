# SDE Console

The Survey Data Exchange (SDE) Console is a component of the Office of National Statistics (ONS) SDE project, which takes an encrypted json payload and transforms it into a number of formats for use within the ONS. This console allows for insertion of input and checking of transformed output files, using the perkin and posie services.

Installation

Using virtualenv and pip, create a new environment and install within using:

	$ pip install -r requirements.txt

It's also possible to install within a container using docker. From the sde-console directory:

	$ docker build -t sde-console .

Usage

To start the console, just run the server, which exposes a server on port 5000:

	$ python server.py

SDE console has two endpoints: the default '/', which takes JSON as input, encrypts it and places it upon the app queue for SDE to decrypt and transform. The '/decrypt' endpoint takes an encrypted payload as input and decrypts to json and transforms to final formats.