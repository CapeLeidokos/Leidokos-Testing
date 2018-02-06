SET CUR_DIR=%~dp0
leidokos_testing_dir="%CUR_DIR%/.."

rem Determine the number of command line arguments
set argC=0
for %%x in (%*) do Set /A argC+=1

if %argC% gtr 1 (
   set git_branch=%2
) else if [%TRAVIS_PULL_REQUEST_BRANCH%] != [] (
   set git_branch=%TRAVIS_PULL_REQUEST_BRANCH%
) else if [%TRAVIS_BRANCH%] != [] (
   set git_branch=%TRAVIS_BRANCH%
) else (
   echo "No testing branch specified, assuming master."
   echo "Note: You can define the environment variable TRAVIS_BRANCH to set the branch."
   set git_branch="master"
)

set python_so_path=C:\msys64\usr\local\lib\libboost_python3.dll
set python_executable=C:\msys64\usr\local\bin\python3.exe
set cmake_executable=C:\msys64\usr\bin\cmake.exe
set ctest_executable=C:\msys64\usr\bin\ctest.exe

%cmake_executable% ^
   "-DLEIDOKOS_TESTING_TARGET_URL=%module_git_url%" ^
   "-DLEIDOKOS_TESTING_TARGET_COMMIT=%git_branch%" ^
   "-DLEIDOKOS_TESTING_TARGET_REPO_IS_FIRMWARE_MODULE=TRUE" ^
   "-DBoost_PYTHON_LIBRARY_RELEASE=%python_so_path%" ^
   "-DBoost_PYTHON_3_LIBRARY_RELEASE=%python_so_path%" ^
   "-DBoost_PYTHON_3_LIBRARY=%python_so_path%" ^
   "-DPYTHON_EXECUTABLE=%python_executable%" ^
   %leidokos_testing_dir%

%cmake_executable% --build .
%ctest_executable% --output-on-failure
