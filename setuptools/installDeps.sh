#!/usr/bin/env bash

set -e

ROOT_UID="0"

#Check if run as root
if [ $EUID -ne 0 ]; then
    echo "This script should be run as root." > /dev/stderr
    exit 1
fi

# install said up-to-date python
apt-get install -y python3 python3-dev build-essential postgresql-client postgresql-common libpq-dev postgresql-9.5 unrar
apt-get install -y postgresql-server-dev-9.5 postgresql-contrib libyaml-dev git phantomjs libffi-dev

# PIL/Pillow support stuff
sudo apt-get install -y libtiff5-dev libjpeg-turbo8-dev zlib1g-dev liblcms2-dev libwebp-dev libxml2 libxslt1-dev

# Install Numpy/Scipy support packages. Yes, scipy depends on FORTAN. Arrrgh
sudo apt-get install -y gfortran libopenblas-dev liblapack-dev


# Install the citext extension
sudo -u postgres psql -c 'CREATE EXTENSION IF NOT EXISTS citext SCHEMA pg_catalog;;'

# I'm not currently using plpython3. Legacy?
# sudo -u postgres psql -c 'CREATE EXTENSION IF NOT EXISTS plpython3u;'

echo Increasing the number of inotify watches.
sudo sysctl -w fs.inotify.max_user_watches=524288
sudo sysctl -p

echo fs.inotify.max_user_watches=524288 >> /etc/sysctl.conf


# Python setup stuff:

# Install pip (You cannot use the ubuntu repos for this, because they will also install python3.2)
wget https://bootstrap.pypa.io/get-pip.py
python3 get-pip.py

# echo TODO: ADD PostgreSQL >= 9.3 install stuff here!

# Install the libraries we actually need
sudo pip3 install --upgrade Mako CherryPy Pyramid Beautifulsoup4 FeedParser colorama
sudo pip3 install --upgrade pyinotify python-dateutil apscheduler rarfile python-magic
sudo pip3 install --upgrade babel cython irc psycopg2 python-levenshtein chardet roman
sudo pip3 install --upgrade python-sql natsort pyyaml pillow rpyc server_reloader selenium
sudo pip3 install --upgrade logging_tree ftfy paramiko irc sqlalchemy
sudo pip3 install --upgrade pysocks statsd pyexecjs

# numpy and scipy are just needed for the image deduplication stuff. They can be left out if
# those functions are not desired.
# And numpy itself
sudo pip3 install --upgrade numpy scipy

# Readability (python 3 port)
sudo pip3 install git+https://github.com/stalkerg/python-readability
sudo pip3 install git+https://github.com/bear/parsedatetime

# Pylzma for 7z support. ~~py3k support is still not in Pypi for no good reason~~
# Never mind. Bugged the dev a bit, and it's now up to date.
sudo pip3 install --upgrade pylzma markdown

sudo pip3 install git+https://github.com/fake-name/UniversalArchiveInterface.git

echo "done"