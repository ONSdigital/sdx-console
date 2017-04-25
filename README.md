# sdx-console

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

| Environment Variable    | Default                               | Description
|-------------------------|---------------------------------------|----------------
| FTP_HOST                | `pure-ftpd`                           | FTP to monitor
| FTP_USER                | _none_                                | User for FTP account if required
| FTP_PASS                | _none_                                | Password for FTP account if required
| ENABLE_EMPTY_FTP        | `0`                                   | `1=on,0=off` Enables the ability to auto-empty the target FTP - **SHOULD NOT BE SWITCHED ON IN A PRODUCTION ENVIRONMENT!**
| EQ_PUBLIC_KEY           | _xxx/xxxx.pem_                        | EQ public key
| EQ_PRIVATE_KEY          | _xxx/xxxx.pem_                        | EQ private key
| EQ_PRIVATE_KEY_PASSWORD | _xxxx_                                | Password for EQ private key
| PRIVATE_KEY             | _xxx/xxxx.pem_                        | Private key
| PRIVATE_KEY_PASSWORD    | _xxxx_                                | Password for private key
| SDX_VALIDATE_URL        | `http://sdx-validate:5000/validate`   | URL of the ``sdx-validate`` service
| SDX_STORE_URL           | `http://sdx-store:5000/`              | URL of the ``sdx-store`` service
| RABBIT_QUEUE            | `survey`                              | Rabbit survey queue
| SDX_FTP_IMAGE_PATH      | `EDC_QImages`                         | FTP Image path
| SDX_FTP_DATA_PATH       | `EDC_QData`                           | FTP Data path
| SDX_FTP_RECEIPT_PATH    | `EDC_QReceipts`                       | FTP Receipt path
| HB_INTERVAL             | '30'                                  | Interval for console heartbeat           
