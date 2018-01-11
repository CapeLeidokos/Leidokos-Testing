# Leidokos-Testing
Leidokos-Testing is a regression testing system for the Kaleidoscope firmware.
It allows to test individual Kaleidoscope modules (core, plugins, etc.).

## CapeLeidokos
Leidokos-Testing is an essential part of the CapeLeidokos build, develop and testing infrastructure for the Kaleidoscope firmware.

<img src="https://github.com/noseglasses/CapeLeidokos/blob/master/CapeLeidokos.svg?sanitize=true">

## Regression testing
Regression testing is of great importance to guarantee and maintain quality of
software projects.

Whenever a bug is discovered and fixed,
an individual test is supposed to be added to the list of regression tests, that asserts the functionality
of the feature affected by the bug. Thus, in case the same bug is accidentaly re-introduced
into the software by future changes, it cannot go undetected.

The philosophy behind regression testing is that one cannot have an infinite number of tests,
nor is it possible to foresee what is going to malfunction. But it is at
least possible to prevent that a bug bites twice.

## Prerequisites
This module depends on a number of other software projects which are listed below. For those projects that require manual installation, install commands for a Ubuntu Linux system
are provided.

* CMake (sudo apt-get install cmake)
* Python (sudo apt-get install python)

There are two other projects, that Leidokos-Testing heavily depends on,
namely [Leidokos-CMake](https://github.com/noseglasses/Leidokos-CMake), used as a convenient build system and [Leidokos-Python](https://github.com/noseglasses/Leidokos-Python),
to generate host specific python modules to wrap a x86 version of the
firmware. These projects are automatically installed by Leidokos-Testing.

## Test specification
Every Kaleidoscope module can define an arbitrary number of tests. These tests are defined through a hierarchical testing file system that is best bundled with the module, so it can be maintained in sync with the changes of the module's implementation.

The testing file system contains information about what functionality to
test as well as what firmware modules appart from the stock firmware are involved in the testing.

Please see the comment section of the file `python/prepare_testing.py`
for a detailed description of the testing file system.

## Under the hood
It can help to understand what the testing system does under the hood. However, it is not necessary to understand the exact mode of operation to generate tests and even less to run tests.

The regression testing process has three stages, a configuration stage, a build stage
and a testing stage.

During the configuration stage, i.e. when CMake is executed:

1. The hierarchial testing file system is parsed via a python script that generates CMake parsable information about what firmware builds are necessary and which tests to run.

2. For every required firmware build a build system target is generated.

3. For every test that is specified, a CTest test is generated

During the build stage, when e.g. `make` is executed a mimimum set of firmwares is build.

During the testing stage, all CTest tests are executed.

Leidokos-Testing detects if several tests are based on a common
firmware build. Such shared firmware configurations are generated only once to safe resources.

## Usage
The regression testing system is designed to operate on a single Kaleidoscope module. It is meant to be part of a continuous integration development process and can easily be triggered, e.g. by [Travis CI](https://travis-ci.org/).

The tested module's git repository URL can be specified through the CMake variable
`LEIDOKOS_TESTING_TARGET_URL` or, alternatively, via the path
to an already cloned version of the module (`LEIDOKOS_TESTING_TREE_ROOT`).

The following example demonstrates how to run the testing system for a ficticiuous Kaleidoscope
module `Kaleidoscope-Transparent-Aluminum`.

```bash
git clone --recursive \
 https://github.com/noseglasses/Leidokos-Testing.git

mkdir testing
cd testing

# Configuration stage
#
cmake -DLEIDOKOS_TESTING_TARGET_URL=<URL of Kaleidoscope-Transparent-Aluminum> \
 ./Leidokos-Testing

# Build stage
#
cmake --build .

# Testing stage
#
ctest
```

## CMake configuration
The following CMake configuration variables affect the behavior of the regression testing system.

| CMake Variable | Description |
|:-------------------------------- |:---------------------------------------- |
| LEIDOKOS_TESTING_TARGET_URL  | The URL of the git repository of the Kaleidoscope module to test |
| LEIDOKOS_TESTING_TARGET_BRANCH | The branch of the target repo to checkout for testing |
| LEIDOKOS_TESTING_TREE_ROOT   | The root directory of the Kaleidoscope module to be tested. This is only effective if LEIDOKOS_TESTING_TARGET_URL is empty. |
| LEIDOKOS_TESTING_AUTO_ADD_TESTED_REPO | This flag defines whether the tested repo is supposed to be automatically added to the firmware build modules |
