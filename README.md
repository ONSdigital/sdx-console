# sdx-console

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/4758006464e4407ca06d263ac2c3eea6)](https://www.codacy.com/app/necrophonic/sdx-console?utm_source=github.com&utm_medium=referral&utm_content=ONSdigital/sdx-console&utm_campaign=badger)
[![Build Status](https://travis-ci.org/ONSdigital/sdx-console.svg?branch=master)](https://travis-ci.org/ONSdigital/sdx-console)

The Survey Data Exchange (SDX) Console is a component of the Office of National Statistics (ONS) SDX project, which takes an encrypted json payload and transforms it into a number of formats for use within the ONS. This console allows for insertion of input and checking of transformed output files, using the sdx-decrypt, sdx-validate, sdx-downstream and sdx-transform-* services.

Should only be deployed on-demand as required in an environment.

## Installation

Checkout the sdx-compose repo and refer to the README

## Usage

To use the console you will need to start all services.

## API

There are two endpoints. The default takes JSON as input, encrypts it and places it upon the app queue for SDE to decrypt and transform, whilst 'decrypt' takes an encrypted payload as input and decrypts to json and transforms to final formats.

 * `POST /`
 * `POST /decrypt`

## Configuration

Some of important environment variables available for configuration are listed below:

| Environment Variable  | Default     | Description
|-----------------------|-------------|----------------
| FTP_HOST              | `pure-ftpd` | FTP to monitor
| FTP_USER              | _none_      | User for FTP account if required
| FTP_PASS              | _none_      | Password for FTP account if required
| ENABLE_EMPTY_FTP      | `0`         | `1=on,0=off` Enables the ability to auto-empty the target FTP - **SHOULD NOT BE SWITCHED ON IN A PRODUCTION ENVIRONMENT!**
