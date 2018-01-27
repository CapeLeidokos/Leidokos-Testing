#!/bin/bash
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

SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
CUR_DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"

if [ "$#" -gt 0 ]; then
   module_git_url=$1
elif [ -n "${TRAVIS_PULL_REQUEST_SLUG}" ]; then
   module_git_url="https://github.com/${TRAVIS_PULL_REQUEST_SLUG}.git"
elif [ -n "${TRAVIS_REPO_SLUG}" ]; then
   module_git_url="https://github.com/${TRAVIS_REPO_SLUG}.git"
else 
   echo "No module git URL specified"
   echo "Either pass the URL as first argument to this script or define"
   echo "one of the environment variable TRAVIS_REPO_SLUG (as owner/repo)"
   exit 1
fi

leidokos_testing_dir="${CUR_DIR}/.."

if [ "$#" -gt 1 ]; then
   git_branch=$2
elif [ -n "${TRAVIS_PULL_REQUEST_BRANCH}" ]; then
   git_branch="${TRAVIS_PULL_REQUEST_BRANCH}"
elif [ -n "${TRAVIS_BRANCH}" ]; then
   git_branch="${TRAVIS_BRANCH}"
else
   echo "No testing branch specified, assuming master."
   echo "Note: You can define the environment variable TRAVIS_BRANCH to set the branch."
   git_branch="master"
fi

if [ "${TRAVIS_OS_NAME}" == "osx" ]; then
   python_so_path="/usr/lib/libboost_python-py34.so"
   if [ ! -f "${python_so_path}" ]; then
      find /usr/lib -name "libboost_python*"
   fi
else
   python_so_path="/usr/lib/x86_64-linux-gnu/libboost_python-py34.so"
fi

cmake \
   "-DLEIDOKOS_TESTING_TARGET_URL=${module_git_url}" \
   "-DLEIDOKOS_TESTING_TARGET_COMMIT=${git_branch}" \
   "-DLEIDOKOS_TESTING_TARGET_REPO_IS_FIRMWARE_MODULE=TRUE" \
   "-DBoost_PYTHON_LIBRARY_RELEASE=${python_so_path}" \
   "-DPYTHON_EXECUTABLE=/usr/bin/python3" \
   ${leidokos_testing_dir}

cmake --build .
ctest --output-on-failure
