#!/bin/bash
# -*- mode: cmake -*-
# Kaleidoscope-Testing -- Testing framework for the Kaleidoscope firmware
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

SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
CUR_DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"

module_git_url=$1

kaleidoscope_testing_dir="${CUR_DIR}/.."

cmake \
   "-DKALEIDOSCOPE_TESTING_TARGET_URL=${module_git_url}" \
   "-DBoost_PYTHON_LIBRARY_RELEASE=/usr/lib/x86_64-linux-gnu/libboost_python-py34.so" \
   "-DPYTHON_EXECUTABLE=/usr/bin/python3" \
   ${kaleidoscope_testing_dir}

cmake --build .
ctest --output-on-failure