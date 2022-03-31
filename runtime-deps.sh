#!/bin/bash
# This file is meant to be run in the Dockerfile to get the runtime dependencies
# if you run it outside, good luck

echo "Getting initial setup dependencies..." 1>&2
apt-get update
apt-get install software-properties-common ca-certificates gnupg curl -y

# add repo that adds libpq properly
echo "Adding repository for libpq..." 1>&2
curl -sS https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor | tee /etc/apt/trusted.gpg.d/apt.postgresql.org.gpg >/dev/null
add-apt-repository "deb http://apt.postgresql.org/pub/repos/apt bullseye-pgdg main"
apt-get update

# install runtime dependencies
echo "Installing runtime dependencies..." 1>&2
apt-get install -y libpq5 tesseract-ocr

# we don't need this crap anymore
echo "Cleaning up..." 1>&2
apt-get remove -y software-properties-common gnupg curl
apt-get autopurge -y
rm -rf /var/lib/apt/lists/*
echo "All runtime dependencies handled!"