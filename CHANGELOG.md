### Unreleased

### 1.7.0 2017-11-30
  - Deploying new console

### 1.6.0 2017-11-21
  - Remove sdx-common logging and move logging code back into the repo
  - Add Cloudfoundry deployment files

### 1.5.1 2017-10-25
  - Add KID hash to the encrypter

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
