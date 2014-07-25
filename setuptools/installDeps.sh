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
apt-get install -y python3.4 python3.4-dev build-essential

# link python3.4 as python3, because ubuntu thinks only python 3.2 is actually python 3
ln -s /usr/bin/python3.4 /usr/bin/python3

# Install pip (You cannot use the ubuntu repos for this, because they will also install python3.2)
wget https://bootstrap.pypa.io/get-pip.py
python3 get-pip.py

# Install the libraries we actually need

pip3 install Mako CherryPy Pyramid Beautifulsoup4 FeedParser colorama pyinotify python-dateutil apscheduler rarfile python-magic babel cython