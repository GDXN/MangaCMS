#!/usr/bin/env bash

ROOT_UID="0"

#Check if run as root
if [ $EUID -ne 0 ]; then
    echo "This script should be run as root." > /dev/stderr
    exit 1
fi

# add PPAs for up-to-date python
add-apt-repository -y ppa:fkrull/deadsnakes
apt-get update

# install said up-to-date python
apt-get install -y python3.4 python3.4-dev build-essential postgresql-client postgresql-common libpq-dev postgresql-9.3 unrar

# PIL/Pillow support stuff
sudo apt-get install -y libtiff4-dev libjpeg-turbo8-dev zlib1g-dev liblcms2-dev libwebp-dev


# link python3.4 as python3, because ubuntu thinks only python 3.2 is actually python 3
# this will possibly (probably?) break things on ubuntu >= 14.04, since that's the version where
# they switched to using python3 for system management stuff.
ln -s /usr/bin/python3.4 /usr/bin/python3

# Install pip (You cannot use the ubuntu repos for this, because they will also install python3.2)
wget https://bootstrap.pypa.io/get-pip.py
python3 get-pip.py

echo TODO: ADD PostgreSQL >= 9.3 install stuff here!

# Install the libraries we actually need
pip3 install Mako CherryPy Pyramid Beautifulsoup4 FeedParser colorama
pip3 install pyinotify python-dateutil apscheduler rarfile python-magic
pip3 install babel cython irc psycopg2 python-levenshtein

# numpy and scipy are just needed for the image deduplication stuff. They can be left out if
# those functions are not desired.

# Install Numpy/Scipy support packages. Yes, scipy depends on FORTAN. Arrrgh
sudo apt-get install -y gfortran libopenblas-dev liblapack-dev

# And numpy itself
pip3 install numpy scipy