# sdx-console

[![Build Status](https://travis-ci.org/ONSdigital/sdx-console.svg?branch=master)](https://travis-ci.org/ONSdigital/sdx-console)

The Survey Data Exchange (SDX) Console is a component of the Office of National Statistics (ONS) SDX project. It will be used to test different microservices in SDX individually and to Reprocess Transactions for Operational Support.

Should only be deployed on-demand as required in an environment.

## Installation
This application presently installs required packages from requirements files:
- `requirements.txt`: packages for the application, with hashes for all packages: see https://pypi.org/project/hashin/ 
- `test-requirements.txt`: packages for testing and linting

It's also best to use `pyenv` and `pyenv-virtualenv`, to build in a virtual environment in the currently recommended version of Python.  To install these, see:
- https://github.com/pyenv/pyenv
- https://github.com/pyenv/pyenv-virtualenv
- (Note that the homebrew version of `pyenv` is easiest to install, but can lag behind the latest release of Python.)

To install, set your Python version using pyenv or similar, and run:
```
make build
```

To test, first run `make build` as above, then run:
```
make test
```
Alternatively, the `sdx-compose` repo allows you to spin up a local test environment for the whole ``sdx-`` suite of services. For more information, refer to the README in `sdx-compose`.

## Usage

To use the console you will need to start all services
Console requires a PostgreSQL database to the appropriate sdx-compose branch should be used

## Authentication

This application uses Flask-Security for login and Flask-Admin for user management

You will need to have an SDX-Console account set up by an administrator to access sdx-console while deployed

Locally one account will be created on launch: 'admin'. This user password is default 'admin'. This user can create developer users.

The login page is located at '/Login'. You can log out at '/Logout'

If you the administrator role you can access the user management AI (Flask-Admin) at '/admin'

## UI

 * `/store` -  allows searching of the PostgreSQL and reprocessing of transactions

## Configuration

Some of important environment variables available for configuration are listed below:

| Environment Variable    | Example                               | Description
|-------------------------|---------------------------------------|----------------
| SDX_STORE_URL           | `http://sdx-store:5000/`              | URL of the ``sdx-store`` service
| CONSOLE_LOGIN_TIMEOUT   | `10`                                  | Number of minutes to user timeout
| CONSOLE_INITIAL_ADMIN_PASSWORD| `PA$$W0RD` | Initial password used for user with admin rights

