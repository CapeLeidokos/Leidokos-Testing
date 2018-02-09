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

if [ "${TRAVIS_OS_NAME}" == "osx" ] || [[ "$OSTYPE" == "darwin"* ]]; then

#    brew list
   brew install ccache
   brew install python3
#    brew install boost --with-python
#    brew info boost-python
   brew install boost-python --with-python3 --without-python
#    sudo easy_install pip3
   sudo -H pip3 install pyyaml
   sudo -H pip3 install sphinx

elif [ "${TRAVIS_OS_NAME}" == "linux" ] || [[ "$OSTYPE" == "linux-gnu" ]]; then
   sudo -H apt-get install -y \
      libboost-python-dev \
      cmake \
      python3-pip \
      python3-yaml

   sudo -H pip3 install sphinx
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
   # package installation for msys2

   #pacman -Ql mingw-w64-x86_64-python3
   #pacman -Ql mingw-w64-x86_64-boost
   pacman --noconfirm -S mingw-w64-x86_64-cmake
   pacman --noconfirm -S mingw-w64-x86_64-python3
   pacman --noconfirm -S mingw-w64-x86_64-python3-pip
   pacman --noconfirm -S mingw-w64-x86_64-boost
   pacman --noconfirm -S mingw-w64-x86_64-ninja
   pacman --noconfirm -S mingw-w64-x86_64-gcc

   python3 /mingw64/bin/pip3-script.py install pyyaml

   # sphinx is only required to build the Leidokos-Python's API
   # python3 /mingw64\bin\pip3-script.py install sphinx
else
	echo "Strange system ${OSTYPE} detected. Unable to setup."
	exit 1
fi