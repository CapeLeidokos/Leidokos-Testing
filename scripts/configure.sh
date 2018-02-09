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
elif [ -n "${APPVEYOR_PULL_REQUEST_HEAD_REPO_NAME}" ]; then
   module_git_url="https://github.com/${APPVEYOR_PULL_REQUEST_HEAD_REPO_NAME}.git"
elif [ -n "${APPVEYOR_REPO_NAME}" ]; then
   module_git_url="https://github.com/${APPVEYOR_REPO_NAME}.git"
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
elif [ -n "${APPVEYOR_PULL_REQUEST_HEAD_REPO_BRANCH}" ]; then
   git_branch="${APPVEYOR_PULL_REQUEST_HEAD_REPO_BRANCH}"
elif [ -n "${APPVEYOR_REPO_BRANCH}" ]; then
   git_branch="${APPVEYOR_REPO_BRANCH}"
else
   echo "No testing branch specified, assuming master."
   echo "Note: You can define the environment variable TRAVIS_BRANCH to set the branch."
   git_branch="master"
fi

if [ "${TRAVIS_OS_NAME}" == "osx" ] || [[ "$OSTYPE" == "darwin"* ]]; then
#    ls -l /usr/local/lib
   python_so_path="/usr/local/lib/libboost_python3.dylib"
   python_executable="/usr/local/bin/python3"
elif [ "${TRAVIS_OS_NAME}" == "linux" ] || [[ "$OSTYPE" == "linux-gnu" ]]; then
   python_so_path="/usr/lib/x86_64-linux-gnu/libboost_python-py34.so"
   python_executable="/usr/bin/python3"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
   python_so_path=/mingw64/bin/libboost_python3-mt.dll
   python_executable=/mingw64/bin/python3.exe
   generator_definition="-G Ninja"
else
	echo "Strange system ${OSTYPE} detected. Unable to build."
	exit 1
fi

cmake \
   ${generator_definition} \
   "-DLEIDOKOS_TESTING_TARGET_URL=${module_git_url}" \
   "-DLEIDOKOS_TESTING_TARGET_COMMIT=${git_branch}" \
   "-DLEIDOKOS_TESTING_TARGET_REPO_IS_FIRMWARE_MODULE=TRUE" \
   "-DBoost_PYTHON_LIBRARY_RELEASE=${python_so_path}" \
   "-DBoost_PYTHON_3_LIBRARY_RELEASE=${python_so_path}" \
   "-DBoost_PYTHON_3_LIBRARY=${python_so_path}" \
   "-DPYTHON_EXECUTABLE=${python_executable}" \
   ${leidokos_testing_dir}
