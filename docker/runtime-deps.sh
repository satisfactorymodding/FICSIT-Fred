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


isDocker(){
    local cgroup=/proc/1/cgroup
    test -f $cgroup && [[ "$(<$cgroup)" = *:cpuset:/docker/* ]]
}

isDockerBuildkit(){
    local cgroup=/proc/1/cgroup
    test -f $cgroup && [[ "$(<$cgroup)" = *:cpuset:/docker/buildkit/* ]]
}

isDockerContainer(){
    [ -e /.dockerenv ]
}

# we don't need this crap anymore
echo "Cleaning up..." 1>&2

if isDockerBuildkit || (isDocker && ! isDockerContainer)
then
  echo "Detected run within docker RUN. Removing apt cache for image size." 1>&2
  apt-get remove -y software-properties-common gnupg curl
  apt-get autopurge -y
  apt-get autoclean -y
  rm -rf /var/lib/apt/lists/*
else
  echo "Opting to not remove stuff so running on real hardware does not break things." 1>&2
fi

echo "All runtime dependencies handled!" 1>&2