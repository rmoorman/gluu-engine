# gluu-flask Cluster Management API Server

## Overview

The gluu-flask server is used to enable management of Gluu Server clusters.
There is an ever-evolving [wiki page](http://www.gluu.co/gluu_salt) which describes
the design of the gluu-flask component.

## Prerequisites

### Ubuntu packages

```
sudo apt-get install -y libssl-dev python-dev swig libzmq3-dev openjdk-7-jre-headless
sudo apt-get build-dep openssl
```

### Install docker

Follow these instructions to install the package for Ubuntu Trusty 14.04 managed by docker.com:
[http://docs.docker.com/installation/ubuntulinux](http://docs.docker.com/installation/ubuntulinux/#docker-maintained-package-installation)

For the impatient, just type:

```
curl -sSL https://get.docker.com/ubuntu/ | sudo sh
```

Note: gluu-flask only supports docker v1.5.0 or above.

### Install salt-master and salt-minion

```
echo deb http://ppa.launchpad.net/saltstack/salt/ubuntu `lsb_release -sc` main | sudo tee /etc/apt/sources.list.d/saltstack.list
wget -q -O- "http://keyserver.ubuntu.com:11371/pks/lookup?op=get&search=0x4759FA960E27C0A6" | sudo apt-key add -
sudo apt-get update
sudo apt-get install -y salt-master salt-minion
```

### License Validator

Get the oxd license validator JAR file:

```
wget http://repo.gluu.org/ubuntu/pool/main/trusty-devel/oxd-license-validator_3.0.1-SNAPSHOT-1_all.deb
sudo dpkg -i oxd-license-validator_3.0.1-SNAPSHOT-1_all.deb
```

### Install weave

Currently `gluu-flask` only supports weave v0.10.0.

```
wget http://repo.gluu.org/ubuntu/pool/main/trusty-devel/weave_0.10.0-1_all.deb
sudo dpkg -i weave_0.10.0-1_all.deb
```

## Deployment

### Install pip and virtualenv

```
wget -q -O- https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py | python -
wget -q -O- https://raw.github.com/pypa/pip/master/contrib/get-pip.py | python -
pip install virtualenv
```

### Clone the project

```
$ git clone https://github.com/GluuFederation/gluu-flask.git
$ cd gluu-flask
$ virtualenv env
$ source env/bin/activate
$ python setup.py install
```

## Configure External Components

`gluu-flask` relies on the following external components:

* weave
* prometheus

Download `postinstall.py` script and run it.
Note: this script will ask `SALT_MASTER_IPADDR` and provider type (`master` or `consumer`) value.

```
wget https://raw.githubusercontent.com/GluuFederation/gluu-cluster-postinstall/master/postinstall.py
python postinstall.py
```

## Run

To run the application in foreground, type the following command in the shell,
and make sure `SALT_MASTER_IPADDR` environment variable is set and
pointed to salt-master IP address.

```
$ source env/bin/activate
$ SALT_MASTER_IPADDR=xxx.xxx.xxx.xxx gluuapi runserver
```

Or, if you have `make` installed

```
$ source env/bin/activate
$ make run
```

## Daemon Mode

To run `gluuapi` in background (daemon mode):

```
$ source env/bin/activate
$ SALT_MASTER_IPADDR=xxx.xxx.xxx.xxx gluuapi daemon --pidfile /path/to/pidfile --logfile /path/to/logfile start
```

The daemon has `start`, `stop`, `restart`, and `status` commands.
It's worth noting that `--pidfile` and `--logfile` must be pointed to accessible (writable and readable) path by user who runs the daemon.
By default they are pointed to `/var/run/gluuapi.pid` and `/var/log/gluuapi.log` respectively.

## Testing

Testcases are running using ``pytest`` executed by ``tox``.

```
pip install tox
tox
```

See `tox.ini` for details.
