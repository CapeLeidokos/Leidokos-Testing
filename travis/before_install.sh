#!/bin/sh
# -*- mode: cmake -*-
# Leidokos-Testing -- Testing framework for the Kaleidoscope firmware
# Copyright (C) 2017 noseglasses (shinynoseglasses@github.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

set -e
set -o xtrace

if [ "${TRAVIS_OS_NAME}" == "osx" ]; then

#    brew list
   brew install python3
#    brew install boost --with-python
   brew install boost-python
#    sudo easy_install pip3
   sudo -H pip3 install pyyaml
   sudo -H pip3 install sphinx

else
   sudo -H apt-get install -y \
      libboost-python-dev \
      cmake \
      python3-pip \
      python3-yaml

   sudo -H pip3 install sphinx
fi