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
 
project(Leidokos-Testing CXX)
cmake_minimum_required(VERSION 2.8)

# Use a custom execute_process wrapper that does proper error reporting 
#
include("${CMAKE_SOURCE_DIR}/cmake/execute_process.macros.cmake")
include("${CMAKE_SOURCE_DIR}/cmake/log.macros.cmake")

set(overall_log_file "${CMAKE_BINARY_DIR}/leidokos_testing.log.txt")

if(EXISTS "${overall_log_file}")
   file(REMOVE "${overall_log_file}")
endif()

set(log_file "${overall_log_file}")

# Define some standard submodules from the Arduino-Boards repo
# that are required for a minimum firmware build
#
set(default_firmware_modules "Kaleidoscope;Kaleidoscope-Ranges")

# We need git to clone remote repositories
#
find_package(Git REQUIRED)

if(NOT GIT_FOUND)
   log(FATAL_ERROR "Unable to find git executable. Please configure the CMake build system manually if git is installed in a non standard location")
endif()

# Consider testing with travis
#
set(default_target_url "")
set(default_target_commit "master")

if(NOT "$ENV{TRAVIS_REPO_SLUG}" STREQUAL "")
   log("Travis testing in progress")
   set(default_target_url "https://github.com/$ENV{TRAVIS_REPO_SLUG}.git")
   if(NOT "$ENV{TRAVIS_PULL_REQUEST_BRANCH}" STREQUAL "")
      set(default_target_commit "$ENV{TRAVIS_PULL_REQUEST_BRANCH}")
   elseif(NOT "$ENV{TRAVIS_COMMIT}" STREQUAL "")
      set(default_target_commit "$ENV{TRAVIS_COMMIT}")
   else()
      log(FATAL_ERROR "No travis commit available")
   endif()
endif()

# The URL of the Kaleidoscope module to test
#
set(LEIDOKOS_TESTING_TARGET_URL "${default_target_url}" CACHE STRING 
   "The URL of a git repository that represents the Kaleidoscope module to test")
   
# If a non-default commit/branch/tag of the target repository is supposed
# to be checked out, this can be set through variable
# LEIDOKOS_TESTING_TARGET_COMMIT.
#
set(LEIDOKOS_TESTING_TARGET_COMMIT "${default_target_commit}" CACHE STRING
   "The git commit/branch/sha of the target module to be checked out for testing")
   
if("${LEIDOKOS_TESTING_TARGET_URL}" STREQUAL "")
   log(FATAL_ERROR "Empty LEIDOKOS_TESTING_TARGET_URL provided")
endif()

log("Target URL: ${LEIDOKOS_TESTING_TARGET_URL}")
log("Target commit: ${LEIDOKOS_TESTING_TARGET_COMMIT}")
      
# The target URL can be an existing path of the local
# file system
#
if(EXISTS "${LEIDOKOS_TESTING_TARGET_URL}")
   log("Testing local module in ${LEIDOKOS_TESTING_TARGET_URL}")
   set(target_module_dir "${LEIDOKOS_TESTING_TARGET_URL}")
   get_filename_component(target_repo_dir_basename 
      "${LEIDOKOS_TESTING_TARGET_URL}" NAME)
else()

   # Or it can be a remote git repository
   
   # Then we have to determine the actual name of the repository (without
   # extension. .../CapeLeidokos/AModule.git would become AModule
   #
   get_filename_component(target_repo_dir_basename 
      "${LEIDOKOS_TESTING_TARGET_URL}" NAME_WE)
      
   # The path where the local copy of the module that is to be tested
   # is going to be checked out.
   #
   set(testing_target_dir "${CMAKE_BINARY_DIR}/target_module")
   file(MAKE_DIRECTORY "${testing_target_dir}")

   # The path to the local copy of the git repository of the module that 
   # is supposed to be tested.
   #
   set(target_module_dir "${testing_target_dir}/${target_repo_dir_basename}")
   
   # Clone the target module
   #
   if(NOT EXISTS "${testing_target_dir}/${target_repo_dir_basename}/.git")
   
      log("Cloning git repository ${LEIDOKOS_TESTING_TARGET_URL}")
      
      _execute_process(
         "clone Kaleidoscope module \"${LEIDOKOS_TESTING_TARGET_URL}\" \
that is supposed to be tested"
         COMMAND "${GIT_EXECUTABLE}" clone 
            "${LEIDOKOS_TESTING_TARGET_URL}"
         WORKING_DIRECTORY "${testing_target_dir}"
      )
   endif()
   
   log("Local target module directory ${target_module_dir}")
   
   _execute_process(
      "check out commit of Kaleidoscope module \
\"${LEIDOKOS_TESTING_TARGET_URL}\" \
that is supposed to be tested"
      COMMAND "${GIT_EXECUTABLE}" checkout ${LEIDOKOS_TESTING_TARGET_COMMIT} 
      WORKING_DIRECTORY "${target_module_dir}"
   )

   # We did not checkout a specific branch during cloning. Therefore
   # we have to update at least the first level of submodules
   # after possibly switching to a different branch (different from master).
   #
   _execute_process(
      "recursively update Kaleidoscope module \"${LEIDOKOS_TESTING_TARGET_URL}\""
      COMMAND "${GIT_EXECUTABLE}" submodule update --init 
      WORKING_DIRECTORY "${target_module_dir}"
   )
   
   # The .gitmodule files of the submodules might have changed. 
   # Thus, we have to syncronize them before doing further updates.
   #
   _execute_process(
      "syncronize submodules of Kaleidoscope module \"${LEIDOKOS_TESTING_TARGET_URL}\""
      COMMAND "${GIT_EXECUTABLE}" submodule sync --recursive 
      WORKING_DIRECTORY "${target_module_dir}"
   )
      
   # Update all submodules recursively.
   #
   _execute_process(
      "recursively update Kaleidoscope module \"${LEIDOKOS_TESTING_TARGET_URL}\""
      COMMAND "${GIT_EXECUTABLE}" submodule update --init --recursive 
      WORKING_DIRECTORY "${target_module_dir}"
   )
endif()

if("${target_repo_dir_basename}" STREQUAL "Leidokos-Python")
   set(target_module_is_leidokos_python TRUE)
   log("Testing Leidokos-Python")
else()
   set(target_module_is_leidokos_python FALSE)
endif()
   
# Normally, the test specifications reside in directories below the
# testing directory of the target module.
# To provide more flexibility, the root of the testing 
# directory structure can be explicitly defined 
# via variable LEIDOKOS_TESTING_TREE_ROOT.
#
set(LEIDOKOS_TESTING_TREE_ROOT 
   "${target_module_dir}/testing" CACHE PATH 
   "The testing directory root of the module to be tested") 
   
if(NOT EXISTS "${LEIDOKOS_TESTING_TREE_ROOT}")
   log(FATAL_ERROR "Unable to find testing tree root \
LEIDOKOS_TESTING_TREE_ROOT=\"${LEIDOKOS_TESTING_TREE_ROOT}\"")
endif()

# Python is needed to parse the testing file system and generate
# CMake compatible information about firmware builds and tests.
#
set(Python_ADDITIONAL_VERSIONS "3")
find_package(PythonInterp REQUIRED)

if(NOT PYTHONINTERP_FOUND)
   log(SEND_ERROR 
"Leidokos-Testing requires a Python3 interpreter to prepare the testing \
infrastructure. If you have installed python in a non standard location, \
please configure the CMake build system accordingly. See the documentation \
about the FindPythonInterp module at \
https://cmake.org/cmake/help/v3.0/module/FindPythonInterp.html \
for additional build system variables that support the python auto \
detection process.")
   log(SEND_ERROR "Under Ubuntu linux python can be installed as")
   log(SEND_ERROR "sudo apt-get install libboost-python-dev")
   log(FATAL_ERROR "Aborting.")
   
endif()

# prepare_testing.py is a python script that scans the testing file
# system and generates a CMake-compatible description of 
# firmware builds and tests to run (cmake_test_definitions_file below).
#
set(prepare_testing_file "${CMAKE_SOURCE_DIR}/python/prepare_testing.py")

set(cmake_test_definitions_file "${CMAKE_BINARY_DIR}/test_definitions.cmake")

# Run Python to prepare the test definition file.
#
_execute_process(
   "prepare test file"
   COMMAND "${PYTHON_EXECUTABLE}" "${prepare_testing_file}"
      -d "${LEIDOKOS_TESTING_TREE_ROOT}"
      -c "${cmake_test_definitions_file}"
)

# The possibly multiple different firmware builds that are needed by 
# the (possibly multiple) tests reside in directories given integer
# numbered names below firmware_builds_base_dir.
#
set(firmware_builds_base_dir "${CMAKE_BINARY_DIR}/firmware")

# Some stuff that needs to be done during build time needs to be
# carried out through CMake scripts that are generated during the 
# configuration stage. All generated CMake scripts reside in 
# directory cmake_scripts_dir.
#
set(cmake_scripts_dir "${CMAKE_BINARY_DIR}/cmake_scripts")

# For every test, an individual log file is generated. Test log files 
# reside in directory test_logs_dir.
#
set(test_logs_dir "${CMAKE_BINARY_DIR}/test_logs")
file(MAKE_DIRECTORY "${test_logs_dir}")

# In the special case that Leidokos-Testing is used to test
# Leidokos-Python, we make sure that the same branch is used
# for the target repository (cloned at the beginning of this file)
# and the Leidokos-Python module used for the firmware.
#
set(leidokos_python_repo_slug "CapeLeidokos/Leidokos-Python")

set(LEIDOKOS_TESTING_LEIDOKOS_PYTHON_URL "https://github.com/${leidokos_python_repo_slug}.git" CACHE STRING
   "Use this variable to define an URL/local path to a Leidokos-Python \
repository that is supposed to be used as firmware module for testing. \
If unspecified, a default repo/commit will be used.")
set(LEIDOKOS_TESTING_LEIDOKOS_PYTHON_COMMIT "master" CACHE STRING
   "Specify a commit that is used together with the repository specified through variable \
LEIDOKOS_TESTING_LEIDOKOS_PYTHON_URL")

set(LEIDOKOS_TESTING_REUSE_TARGET_LEIDOKOS_PYTHON FALSE CACHE BOOL
   "If this variable is enabled, the target repository is used as \
Leidokos-Python. Make sure that you only enable this variable it you are \
testing Leidokos-Python (target).")

# The default Leidokos-Python to use as firmware module (possibly
# replaced below)
#
set(leidokos_python_url "${LEIDOKOS_TESTING_LEIDOKOS_PYTHON_URL}")
set(leidokos_python_commit "${LEIDOKOS_TESTING_LEIDOKOS_PYTHON_COMMIT}")

if(LEIDOKOS_TESTING_REUSE_TARGET_LEIDOKOS_PYTHON)

   # Use the target repository as Leidokos-Python.
   #
   set(leidokos_python_url "${LEIDOKOS_TESTING_TARGET_URL}")
   set(leidokos_python_commit "${LEIDOKOS_TESTING_TARGET_COMMIT}")
endif()

# An auxiliary function that helps us to determine the firmware build 
# directory for a given build ID.
#
function(_determine_firmware_build_dir
   build_id_
   result_var_
)
   set(firmware_dir "${firmware_builds_base_dir}/${build_id_}")
   set("${result_var_}" "${firmware_dir}/build" PARENT_SCOPE)
endfunction()

# An auxiliary method to report configuration errors for specific
# firmware builds.
#
function(_configuration_error_build
   build_id_
)
   log(FATAL_ERROR "kaleidoscope_firmware_build (BUILD_ID=${build_id_}): ${ARGN}")
endfunction()

# An auxiliary macro that defines a git repository, a commit and a module
# name and adds them to a list of modules.
#
# TODO: Check URLs for uniqueness.
#
macro(_add_firmware_module
   url_
   commit_
   name_
)
   list(APPEND args_URL "${url_}")
   
   if(NOT "${commit_}" STREQUAL "")
      list(APPEND args_COMMIT "${commit_}")
   else()
      list(APPEND args_COMMIT "__NONE__")
   endif()
   
   if(NOT "${name_}" STREQUAL "")
      list(APPEND args_NAME "${name_}")
   else()
      list(APPEND args_NAME "__NONE__")
   endif()
endmacro()

# This function is called from the generated file cmake_test_definitions_file
# that is included further on.
#
# It generates a CMake target to build a Kaleidoscope firmware based
# on a given firmware sketch and a specific module configuration.
#
function(kaleidoscope_firmware_build)

   # Parse variadic arguments
   #
   set(options "")
   set(one_value_args 
      "BUILD_ID" "DIGEST" "FIRMWARE_SKETCH" "BOARDS_URL" "BOARDS_COMMIT")
   set(multi_value_args "URL" "COMMIT" "NAME")
   
   cmake_parse_arguments(args 
      "${options}" "${one_value_args}" "${multi_value_args}" ${ARGN} )
      
   # Check consistency of call arguments.
   #
   if("${args_BUILD_ID}" STREQUAL "")
      _configuration_error_build(${args_BUILD_ID} "BUILD_ID undefined")
   endif()
   
   if("${args_FIRMWARE_SKETCH}" STREQUAL "")
      _configuration_error_build(${args_BUILD_ID} "FIRMWARE_SKETCH undefined")
   endif()
   
   # Generate an absolute firmware build directory based on the build ID.
   #
   _determine_firmware_build_dir("${args_BUILD_ID}" firmware_build_dir)
   file(MAKE_DIRECTORY "${firmware_build_dir}")
   
   set(configure_log_file "${firmware_build_dir}/leidokos-testing.configure.log.txt")
   set(build_log_file "${firmware_build_dir}/leidokos-testing.build.log.txt")
   
   if(EXISTS "${configure_log_file}")
      file(REMOVE "${configure_log_file}")
   endif()
   
   set(log_file "${configure_log_file}")
   
   log("Preparing firmware build in ${firmware_build_dir}")
   
   # Prepare the firmware directory
   #
   file(MAKE_DIRECTORY "${firmware_build_dir}/hardware/keyboardio")
      
   # Set the default boards URL and commit if none is specified.
   #
   if("${args_BOARDS_URL}" STREQUAL "")
      set(args_BOARDS_URL "https://github.com/CapeLeidokos/Arduino-Boards.git")
   endif()
   
   if("${args_BOARDS_COMMIT}" STREQUAL "")
      set(args_BOARDS_COMMIT "origin/regression_testing")
   endif()
   
   log("   Sketch: ${args_FIRMWARE_SKETCH}")
   log("   Boards url: ${args_BOARDS_URL}")
   log("   Boards commit: ${args_BOARDS_COMMIT}")
   
   # Only clone and checkout the boards directory once. 
   # During consecutive configuration runs, modules 
   # will be updated individually.
   #
   if(NOT EXISTS "${firmware_build_dir}/hardware/keyboardio/avr")
      
      _execute_process(
         "clone ${args_BOARDS_URL}"
         COMMAND "${GIT_EXECUTABLE}" clone "${args_BOARDS_URL}"
            hardware/keyboardio/avr
         WORKING_DIRECTORY "${firmware_build_dir}"
      )
      
      _execute_process(
         "check out ${args_BOARDS_COMMIT}"
         COMMAND "${GIT_EXECUTABLE}" checkout
            "${args_BOARDS_COMMIT}"
         WORKING_DIRECTORY "${firmware_build_dir}/hardware/keyboardio/avr"
      )      
      
      _execute_process(
         "syncronize boards submodules"
         COMMAND "${GIT_EXECUTABLE}" submodule sync
         WORKING_DIRECTORY "${firmware_build_dir}/hardware/keyboardio/avr"
      )
      
      log("   Boards default firmware modules")
      
      function(_update_submodule
         module_name_
      )
         _execute_process(
            "update boards submodules"
            COMMAND "${GIT_EXECUTABLE}" submodule update --init "libraries/${module_name_}"
            WORKING_DIRECTORY "${firmware_build_dir}/hardware/keyboardio/avr"
         )
      
         _execute_process(
            "syncronize boards submodules"
            COMMAND "${GIT_EXECUTABLE}" submodule sync --recursive
            WORKING_DIRECTORY "${firmware_build_dir}/hardware/keyboardio/avr/libraries/${module_name_}"
         )
      
         _execute_process(
            "update boards submodules"
            COMMAND "${GIT_EXECUTABLE}" submodule update --init --recursive
            WORKING_DIRECTORY "${firmware_build_dir}/hardware/keyboardio/avr/libraries/${module_name_}"
         )
      endfunction()
      
      foreach(default_module ${default_firmware_modules})
      
         log("      ${default_module}")
         _update_submodule("${default_module}")
      endforeach()
   else()
      log("   Boards default firmware modules")
      foreach(default_module ${default_firmware_modules})
         log("      ${default_module}")
      endforeach()
   endif()
   
   set(LEIDOKOS_TESTING_TARGET_REPO_IS_FIRMWARE_MODULE FALSE CACHE BOOL
      "It this flag is enabled, the target repository is automatically added "
      "to the firmware modules")
      
   if(LEIDOKOS_TESTING_TARGET_REPO_IS_FIRMWARE_MODULE)
      log("   Adding target ${LEIDOKOS_TESTING_TARGET_URL} to firmware modules")
      _add_firmware_module(
         "${LEIDOKOS_TESTING_TARGET_URL}"
         "${LEIDOKOS_TESTING_TARGET_COMMIT}"
         "${target_repo_dir_basename}"
      )
   endif()
   
   # Leidokos-Python is needed by all builds to ensure that 
   # we can build firmware libraries for the host target that
   # can be used by our python drivers
   #
   if(   
         # Make sure that we do not redundantly add Leidokos-Python as firmware
         # module.
         
         (NOT "${leidokos_python_url}" STREQUAL 
                  "${LEIDOKOS_TESTING_TARGET_URL}")
      OR (NOT LEIDOKOS_TESTING_TARGET_REPO_IS_FIRMWARE_MODULE)
   )
      log("   Adding default ${leidokos_python_url} to firmware modules")
      _add_firmware_module(
         "${leidokos_python_url}"
         "${leidokos_python_commit}"
         ""
      )
   endif()
   
   # Tests can specify firmware modules that are
   # supposed to be build and linked additionally to the default board
   # modules. For each module a tuple of URL, commit (commit/tag/branch)
   # and a module name can be specified. If one is specified, all there
   # are needed. That's why we have to ensure that the numbers of provided
   # URLs, commits and names match.
   #
   list(LENGTH args_URL n_urls)
   list(LENGTH args_COMMIT n_commits)
   list(LENGTH args_NAME n_names)
   
   if(NOT n_urls EQUAL n_commits)
      _configuration_error_build(${args_BUILD_ID} 
         "The number of URLs and commits must match. \
There are ${n_urls} URLs (${args_URL}) and ${n_commits} (${args_COMMIT}) commits registered")
   endif()
   
   if(NOT n_urls EQUAL n_names)
      _configuration_error_build(${args_BUILD_ID} 
         "The number of URLs and names must match")
   endif()
   
   set(boards_dir 
      "${firmware_build_dir}/hardware/keyboardio/avr")
   
   set(firmware_libraries_dir 
      "${boards_dir}/libraries")
   
   if(n_urls GREATER 0)
   
      # Add explicitly specified firmware modules.

      log("   Non-default modules:")
   
      math(EXPR max_id "${n_urls} - 1")
   
      # Every module corresponds to a directory in 
      # hardware/keyboardio/avr/libraries. 
      #
      foreach(id RANGE ${max_id})
      
         list(GET args_URL ${id} url)
         list(GET args_COMMIT ${id} commit)
         list(GET args_NAME ${id} module_name)
         
         if("${commit}" STREQUAL "__NONE__")
            set(commit "origin/master")
         endif()
         if("${module_name}" STREQUAL "__NONE__")
            set(module_name "")
         endif()
         
         macro(_clone_firmware_module_if_non_existent) 
         
            # We clone only once (if the module directory does not yet exist).
            #
            if(NOT EXISTS "${firmware_libraries_dir}/${module_name}")
            
               log("      Cloning module ${url}")
               _execute_process(
                  "clone Kaleidoscope module \"${url}\""
                  COMMAND "${GIT_EXECUTABLE}" clone
                     "${url}" "${module_name}"
                  WORKING_DIRECTORY "${firmware_libraries_dir}"
               )
            endif()
         endmacro()
         
         macro(_fetch_firmware_module)
               
            log("      Fetching remote of module ${module_name}")
            _execute_process(
               "fetch remote of module ${module_name}"
               COMMAND "${GIT_EXECUTABLE}" fetch 
               WORKING_DIRECTORY "${firmware_libraries_dir}/${module_name}"
            )
         endmacro()
         
         macro(_update_firware_module)
         
            # If a commit is defined, it is checked out and all git submodules
            # are updated.
            #
            log("      Checking out ${commit} of module ${module_name}")
            _execute_process(
               "check out commit ${commit} in module ${module_name}"
               COMMAND "${GIT_EXECUTABLE}" checkout ${commit}
               WORKING_DIRECTORY "${firmware_libraries_dir}/${module_name}"
            )
            
            if(IS_DIRECTORY "${firmware_libraries_dir}/${module_name}/.git")
            
               # The module is a submodule by itself
               
               _execute_process(
                  "update module ${module_name} recursively"
                  COMMAND "${GIT_EXECUTABLE}" submodule update --init
                  WORKING_DIRECTORY "${firmware_libraries_dir}/${module_name}"
               )
               _execute_process(
                  "syncronize submodules of module ${module_name}"
                  COMMAND "${GIT_EXECUTABLE}" submodule sync --recursive
                  WORKING_DIRECTORY "${firmware_libraries_dir}/${module_name}"
               )
               _execute_process(
                  "update module ${module_name} recursively"
                  COMMAND "${GIT_EXECUTABLE}" submodule update --init --recursive
                  WORKING_DIRECTORY "${firmware_libraries_dir}/${module_name}"
               )
            else()
            
               # The module is a submodule of Arduino-Boards
               
               _execute_process(
                  "update module ${module_name} recursively"
                  COMMAND "${GIT_EXECUTABLE}" submodule update --init -- "libraries/${module_name}"
                  WORKING_DIRECTORY "${boards_dir}"
               )
               _execute_process(
                  "syncronize submodules of module ${module_name}"
                  COMMAND "${GIT_EXECUTABLE}" submodule sync --recursive -- "libraries/${module_name}"
                  WORKING_DIRECTORY "${boards_dir}"
               )
               _execute_process(
                  "update module ${module_name} recursively"
                  COMMAND "${GIT_EXECUTABLE}" submodule update --init --recursive -- "libraries/${module_name}"
                  WORKING_DIRECTORY "${boards_dir}"
               )
            
            endif()
            
         endmacro()
         
         macro(_remove_firmware_module
            module_name_
         )
            log("      Removing pre-existing module ${module_name_}")

            file(REMOVE_RECURSE "${firmware_libraries_dir}/${module_name_}")
         endmacro()
         
         if("${module_name}" STREQUAL "")
         
            # If no module name (NAME) is provided, a module is cloned 
            # by its URL and possibly its COMMIT.
         
            if("${url}" STREQUAL "")
               _configuration_error_build(${args_BUILD_ID} 
                  "A module specification with both an empty URL \
and an empty NAME has been provided.")
            endif()
            
            get_filename_component(module_name "${url}" NAME_WE) 
            
            _clone_firmware_module_if_non_existent()
            _update_firware_module()

         else()
            if("${url}" STREQUAL "")
               _fetch_firmware_module()
            else()
               _clone_firmware_module_if_non_existent()
            endif()
               
            _update_firware_module()
         endif()
            
      endforeach()
   endif()
   
   # Kaleidoscope modules can define a setup script (setup_library.script.cmake)
   # that must be run 
   # once, before the firmware can be build (non-arduino conformant).
   # 
   set(setup_library_script_basename "setup_library.script.cmake")
   
   # Search modules for setup scripts and execute those that are found.
   #
   file(GLOB library_dirs 
      "${firmware_build_dir}/hardware/keyboardio/avr/libraries/*")
   
   foreach(lib_dir ${library_dirs})
   
      set(setup_script "${lib_dir}/${setup_library_script_basename}")
      
      if(EXISTS "${setup_script}")
      
         log("   Setting up firmware module ${lib_dir}")
         
         _execute_process(
            "setup library in ${lib_dir}"
            COMMAND "${CMAKE_COMMAND}"
               "-DCMAKE_SOURCE_DIR=${lib_dir}"
               "-DKALEIDOSCOPE_VIRTUAL_BUILD=TRUE"
               -P "${setup_script}"
            WORKING_DIRECTORY "${lib_dir}"
         )
      endif()
   endforeach()
   
   # To be portable, we use CMake scripts during the build phase.
   #
   set(firmware_build_script 
      "${cmake_scripts_dir}/build_firmware_${args_BUILD_ID}.script.cmake")
      
   # We pass certain variables that are specified at the command line of
   # Leidokos-Testing, on to Leidokos-Python that is configured during 
   # the build process.
   #
   set(leidokos_python_cmd_line_vars "")
   
   # An auxiliary function to add CMake variables of this Leidokos-Testing 
   # configuration process as Leidokos-Python CMake command line arguments.
   #
   function(_init_cmake_variable
      var_
   )
      if("${${var_}}" STREQUAL "")
         return()
      endif()
      
      set("leidokos_python_cmd_line_vars" 
         "${leidokos_python_cmd_line_vars} -D${var_}=${${var_}}" PARENT_SCOPE)
   endfunction()
   
   _init_cmake_variable(Boost_DIR)
   _init_cmake_variable(Boost_INCLUDE_DIR)
   _init_cmake_variable(Boost_LIBRARY_DIR_DEBUG)
   _init_cmake_variable(Boost_LIBRARY_DIR_RELEASE)
   _init_cmake_variable(Boost_PYTHON_LIBRARY_DEBUG)
   _init_cmake_variable(Boost_PYTHON_LIBRARY_RELEASE)
   _init_cmake_variable(PYTHON_INCLUDE_DIR)
   _init_cmake_variable(PYTHON_LIBRARY)
   _init_cmake_variable(PYTHON_LIBRARY_DEBUG)
   
   # Generate the firmware build script.
   #
   file(WRITE "${firmware_build_script}" "\
include(\"${CMAKE_SOURCE_DIR}/cmake/execute_process.macros.cmake\")
include(\"${CMAKE_SOURCE_DIR}/cmake/log.macros.cmake\")

file(REMOVE \"\${log_file}\")

_execute_process(
   \"configure firmware build ${args_BUILD_ID}\"
   COMMAND \"${CMAKE_COMMAND}\" 
      \"-DKALEIDOSCOPE_FIRMWARE_SKETCH=${args_FIRMWARE_SKETCH}\"
      ${leidokos_python_cmd_line_vars}
      \"${firmware_libraries_dir}/Leidokos-Python\"
   WORKING_DIRECTORY \"${firmware_build_dir}\"
)

_execute_process(
   \"generate firmware build ${args_BUILD_ID}\"
   COMMAND \"${CMAKE_COMMAND}\" --build .
   WORKING_DIRECTORY \"${firmware_build_dir}\"
)
")

   set(firmware_binary "${firmware_build_dir}/kaleidoscope.firmware")
   
   add_custom_command(
      OUTPUT "${firmware_binary}"
      COMMAND "${CMAKE_COMMAND}" 
         "-Dlog_file=${build_log_file}" -P "${firmware_build_script}"
      COMMENT "Building Kaleidoscope firmware ${args_BUILD_ID} \
(\"${firmware_build_dir}\")"
   )
   
   # Define a CMake-target to build the firmware
   #
   add_custom_target(
      firmware_${args_BUILD_ID}
      ALL
      DEPENDS "${firmware_binary}"
   )
endfunction() # end of kaleidoscope_firmware_build

# An error reporting function for test specifications
#
function(_kaleidoscope_test_error
   name_
)
   log(FATAL_ERROR "kaleidoscope_test (NAME=${name_}): ${ARGN}")
endfunction()

# This function is called from the generated file ${cmake_test_definitions_file}.
#
# It defines a firmware test that is based on a given python driver file
# and operates on a specific firmware build.
#
function(kaleidoscope_test)
   
   # Errors during test configuration are logged to the global log file.
   #
   set(log_file "${overall_log_file}")
   
   # Parse variadic arguments
   #
   set(options "")
   set(one_value_args "TEST_NAME" "PYTHON_DRIVER" 
      "DRIVER_CMD_LINE_FLAGS" "FIRMWARE_BUILD_ID"
      
      # The following arguments are unused (and silently ignored)
      "TEST_ID" "TEST_DESCRIPTION" "NAME_ORIGIN" "DESCRIPTION_ORIGIN"
      "DRIVER_CMD_LINE_FLAGS_ORIGIN"
      "FIRMWARE_BUILD_ORIGIN")
   set(multi_value_args "")
   
   cmake_parse_arguments(args "${options}" "${one_value_args}" "${multi_value_args}" ${ARGN} )
   
   macro(_assert_test_args_defined 
      arg_names_
   )
      foreach(arg_name ${arg_names_})
         if("${args_${arg_name}}" STREQUAL "")
            _kaleidoscope_test_error("${args_TEST_NAME}" "${arg_name} undefined")
         endif()
      endforeach()
   endmacro()
   
   # Check argument consistency
   #
   _assert_test_args_defined("TEST_NAME;PYTHON_DRIVER;FIRMWARE_BUILD_ID")

   _determine_firmware_build_dir("${args_FIRMWARE_BUILD_ID}" firmware_build_dir)
   
   log("Adding test ${args_TEST_NAME}")
   
   # Tests are run by CTest. To be portable, we use a CMake script to 
   # drive the test that is generated during configuration.
   #
   set(test_driver_script 
      "${cmake_scripts_dir}/run_test_${args_TEST_ID}.script.cmake")
      
   # If we are currently testing Leidokos-Python, we want the firmware
   # to depend on 
   if(   target_module_is_leidokos_python
     AND LEIDOKOS_TESTING_TARGET_REPO_IS_FIRMWARE_MODULE
   )
      set(leidokos_python_module_search_path "${target_module_dir}/python")
   else()
      set(leidokos_python_module_search_path "${firmware_build_dir}/hardware/keyboardio/avr/libraries/Leidokos-Python/python")
   endif()
      
   file(WRITE "${test_driver_script}" 
"\
include(\"${CMAKE_SOURCE_DIR}/cmake/execute_process.macros.cmake\")
include(\"${CMAKE_SOURCE_DIR}/cmake/log.macros.cmake\")

set(log_file \"${test_logs_dir}/${args_TEST_NAME}.log\")
file(REMOVE \"\${log_file}\")

set(ENV{PYTHONPATH} \"${firmware_build_dir}:${leidokos_python_module_search_path}\")

log(\"PYTHONPATH = \$ENV{PYTHONPATH}\")

_execute_process(
   \"run test firmware build ${args_TEST_ID}\"
   RESULT_VARIABLE test_result
   COMMAND \"${PYTHON_EXECUTABLE}\" \"${args_PYTHON_DRIVER}\" ${args_DRIVER_CMD_LINE_FLAGS} 
   WORKING_DIRECTORY \"${firmware_build_dir}\"
)

if(NOT \${test_result} EQUAL 0)
   log(FATAL_ERROR \"Test failed\")
endif()
")
   
   # Register the test with CTest.
   #
   add_test(
      NAME "${args_TEST_NAME}"
      COMMAND "${CMAKE_COMMAND}" -P "${test_driver_script}"
   )
endfunction() # end of kaleidoscope_test

# Enable testing with CTest
#
enable_testing()

# When including the test definition file, a number of calls 
# to kaleidoscope_firmware_build(...) and kaleidoscope_test(...)
# are executed and firmware builds and tests are registered.
#
include("${cmake_test_definitions_file}")
