# sdx-console

[![Build Status](https://travis-ci.org/ONSdigital/sdx-console.svg?branch=master)](https://travis-ci.org/ONSdigital/sdx-console)

The Survey Data Exchange (SDX) Console is a component of the Office of National Statistics (ONS) SDX project, which takes an encrypted json payload and transforms it into a number of formats for use within the ONS. This console allows for insertion of input and checking of transformed output files, using the sdx-decrypt and sdx-validate services.

## Usage

To use the console you will need to start all services.

To get the environment running:

  - ./init.sh  # clones submodules
  - ./update.sh  # pulls the latest version of each submodule, runs `mvn package` in the `perkin` project and calls `docker-compose up`

After a `docker-compose up`, the `sdx-console` app will be exposed on the host ip address (on port 80).

SDE console has two endpoints: the default '/', which takes JSON as input, encrypts it and places it upon the app queue for SDE to decrypt and transform. The '/decrypt' endpoint takes an encrypted payload as input and decrypts to json and transforms to final formats.

