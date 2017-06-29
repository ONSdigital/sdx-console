# sdx-console

[![Build Status](https://travis-ci.org/ONSdigital/sdx-console.svg?branch=master)](https://travis-ci.org/ONSdigital/sdx-console)

The Survey Data Exchange (SDX) Console is a component of the Office of National Statistics (ONS) SDX project. It will be used to test different microservices in SDX individually and to Reprocess Transactions for Operational Support.

Should only be deployed on-demand as required in an environment.

## Installation

Checkout the sdx-compose repo and refer to the README

## Usage

To use the console you will need to start all services
Console requires a PostgreSQL database to the appropriate sdx-compose branch should be used

## Authentication

This application uses Flask-Security for login and Flask-Admin for user management

You will need to have an SDX-Console account set up by an administrator to access sdx-console while deployed

Locally three accounts will be created on launch: 'admin', 'dev', and 'none'. With differing levels of permissions. All three have the password 'password'

The login page is located at '/Login'. You can log out at '/Logout'

If you the administrator role you can access the user management AI (Flask-Admin) at '/admin'

## UI

 * `/decrypt` - provides a textbox to input encrypted data which can be POSTed to the sdx-decrypt service

 * `/store` -  allows searching of the PostgreSQL and reprocessing of transactions

## Configuration

Some of important environment variables available for configuration are listed below:

| Environment Variable    | Example                               | Description
|-------------------------|---------------------------------------|----------------
| SDX_DECRYPT_URL         | `http://sdx-decrypt:5000/`            | URL of the ``sdx-decrypt`` service
| SDX_STORE_URL           | `http://sdx-store:5000/`              | URL of the ``sdx-store`` service
| HB_INTERVAL             | `30`                                  | Interval for console heartbeat        
| CONSOLE_LOGIN_TIMEOUT   | `10`                                  | Number of minutes to user timeout   
