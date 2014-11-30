#!/usr/bin/env bash

ROOT_UID="0"

#Check if run as root
if [ $EUID -ne 0 ]; then
    echo "This script should be run as root." > /dev/stderr
    exit 1
fi

# install said up-to-date python
apt-get install -y python3.4 python3.4-dev build-essential postgresql-client postgresql-common libpq-dev postgresql-9.3 unrar
apt-get install -y postgresql-server-dev-9.3 postgresql-contrib libyaml-dev git

# PIL/Pillow support stuff
sudo apt-get install -y libtiff4-dev libjpeg-turbo8-dev zlib1g-dev liblcms2-dev libwebp-dev libxml2 libxslt1-dev

# Install pip (You cannot use the ubuntu repos for this, because they will also install python3.2)
wget https://bootstrap.pypa.io/get-pip.py
python3 get-pip.py

echo TODO: ADD PostgreSQL >= 9.3 install stuff here!

# Install the libraries we actually need
pip3 install Mako CherryPy Pyramid Beautifulsoup4 FeedParser colorama
pip3 install pyinotify python-dateutil apscheduler rarfile python-magic
pip3 install babel cython irc psycopg2 python-levenshtein
pip3 install python-sql natsort pyyaml pillow rpyc server_reloader

# numpy and scipy are just needed for the image deduplication stuff. They can be left out if
# those functions are not desired.

# Install Numpy/Scipy support packages. Yes, scipy depends on FORTAN. Arrrgh
sudo apt-get install -y gfortran libopenblas-dev liblapack-dev

# And numpy itself
pip3 install numpy scipy

# Readability (python 3 port)
sudo pip3 install git+https://github.com/stalkerg/python-readability
sudo pip3 install git+https://github.com/bear/parsedatetime

# Pylzma for 7z support. py3k support is still not in Pypi for no good reason
sudo pip3 install pylzma

sudo pip3 install git+https://github.com/fake-name/UniversalArchiveInterface.git

# Install the citext extension
sudo -u postgres psql -c 'CREATE EXTENSION IF NOT EXISTS citext;'

# I'm not currently using plpython3. Legacy?
# sudo -u postgres psql -c 'CREATE EXTENSION IF NOT EXISTS plpython3u;'

echo Increasing the number of inotify watches.
sysctl -w fs.inotify.max_user_watches=524288
sysctl -p

echo fs.inotify.max_user_watches=524288 >> /etc/sysctl.conf
