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
 
 project(Kaleidoscope-Testing)

find_package(Git REQUIRED)

if(NOT GIT_FOUND)
   message(FATAL_ERROR "Unable to find git executable. Please configure the CMake build system manually if git is installed in a non standard location")
endif()

# The URL of the Kaleidoscope module to test can be parsed via
#
set(KALEIDOSCOPE_TESTING_TARGET_URL "" CACHE STRING 
   "The URL of a git repository that represents the Kaleidoscope module to test")

if("${KALEIDOSCOPE_TESTING_TARGET_URL}" STREQUAL "")
   message(FATAL_ERROR "No valid KALEIDOSCOPE_TESTING_TARGET_URL defined")
endif()

get_filename_component(target_repo_dir_basename 
   "${KALEIDOSCOPE_TESTING_TARGET_URL}" NAME_WE)

set(testing_target_dir "${CMAKE_BINARY_DIR}/target_module")

# Clone the target module, i.e. the module that is supposed to be tested
#
if(NOT EXISTS "${testing_target_dir}/${target_repo_dir_basename}/.git")
   message("Cloning git repository ${KALEIDOSCOPE_TESTING_TARGET_URL}")
   execute_process(
      COMMAND "${GIT_EXECUTABLE}" clone "${KALEIDOSCOPE_TESTING_TARGET_URL}"
      WORKING_DIRECTORY "${testing_target_dir}"
   )
else()
   message("Git repository already cloned to ${testing_target_dir}/${target_repo_dir_basename}")
endif()

set(cmake_testing_specification 
   "${CMAKE_BINARY_DIR}/cmake_testing_specification.include.cmake")
   
set(KALEIDOSCOPE_TESTING_TARGET_MODULE_DIR "" CACHE PATH 
   "The root directory of the module to be tested")
   
set(KALEIDOSCOPE_TESTING_TREE_ROOT "${KALEIDOSCOPE_TESTING_TARGET_MODULE_DIR}/testing" CACHE PATH 
   "The testing directory root of the module to be tested") 

find_package(PythonInterp REQUIRED)

if(NOT PYTHONINTERP_FOUND)
   message(SEND_ERROR "Kaleidoscope-Testing requires a Python interpreter to prepare the testing infrastructure. If you have installed python in a non standard location, please configure the CMake build system accordingly. See the documentation about the FindPythonInterp module at https://cmake.org/cmake/help/v3.0/module/FindPythonInterp.html for additional build system variables that support the python auto detection process.")
   message(SEND_ERROR "Under Ubuntu linux python can be installed as")
   message(SEND_ERROR "sudo apt-get install libboost-python-dev")
   message(FATAL_ERROR "Aborting.")
   
endif()
... this is something that might better be done using python?

# If all this is done, we have a list of tests
# 
# Each test is defined by
# 
# - a python driver file
# - a sketch (.ino
# - a test specification
#    - name (unique)
#    - description
#    - list of dependent modules (a list of modules the test firmware requires to build)

# To have as little to build as possible, all those tests, that use the same modules
# should share a common build target

# It is also necessary to automatically add the Kaleidoscope-Python-Wrapper plugin to all lists of dependent modules

# For every independent set of modules add a build target

# For every test add a CTest test that uses the firmware that matches and the respective python  
#    test driver

# Build is then done with make or whatever other build system

# Testing is carried out via CTest