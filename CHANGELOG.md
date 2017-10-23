### Unreleased
  - Log version number on startup, at info level
  - Add configurable log level
  - Add change log
  - Fix [#36](https://github.com/ONSdigital/sdx-console/issues/36) crash/hang when FTP takes too long to respond
  - Fix [#37](https://github.com/ONSdigital/sdx-console/issues/37) incorrect "Enable empty FTP" setting - now off by default
  - Add QBS template
  - Add all environment variables to README
  - Removed old functionality
  - Added heartbeat
  - Added unittests
  - Added new decrypt functionality with unit tests
  - Added Authentication with flask_security
  - Added Account Management with flask_admin
  - Added database.py for handling PostgreSQL
  - Added Search functionality for sdx-store at /store
  - Adding sdx-common functionality
  - Updating logger format using sdx-common
  - Adding reprocessing functionality
  - Updating reprocessing functionality, removing queuepublisher and encrypter
  - Added Pagination
  - Added auditable logging
  - Added searching by valid/invalid
  - Added protection on "reprocess all" button
  - Add ability to add multiple user accounts dynamically
  - Improved login/out navigation
  - Fix login functionality with compose

### 1.5.0 2017-09-14
  - Remove sdx-common git clone in Dockerfile

### 1.4.0 2017-08-04
  - Add MakeFile

### 1.3.0 2017-07-25
  - Update example json for EQ Survey refresh
  - Change all instances of ADD to COPY in Dockerfile

### 1.2.0 2017-07-10
  - Adding tx_id to the message headers
  - Log version number on startup, at info level
  - Add configurable log level
  - Add change log
  - Fix [#36](https://github.com/ONSdigital/sdx-console/issues/36) crash/hang when FTP takes too long to respond
  - Fix [#37](https://github.com/ONSdigital/sdx-console/issues/37) incorrect "Enable empty FTP" setting - now off by default
  - Add QBS template
  - Add all environment variables to README
  - Remove secure data from logging messages
  - Add license
  - Adding sdx-common functionality
  - Updating logger format using sdx-common
  - Update and pin version of sdx-common to 0.7.0

### 1.0.0 2016-08-16
  - Initial release
