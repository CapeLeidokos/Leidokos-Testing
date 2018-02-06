set CUR_DIR=%~dp0
set leidokos_testing_dir="%CUR_DIR%\.."

rem Determine the number of command line arguments
set argC=0
for %%x in (%*) do Set /A argC+=1

if %argC% gtr 0 (
   set module_git_url=%1
) else if not [%APPVEYOR_PULL_REQUEST_HEAD_REPO_NAME%] == [] (
   set module_git_url="https://github.com/%APPVEYOR_PULL_REQUEST_HEAD_REPO_NAME%.git"
) else if not [%APPVEYOR_REPO_NAME%] == [] (
   set module_git_url="https://github.com/%APPVEYOR_REPO_NAME%.git"
) else (
   echo "No module git URL specified"
   echo "Either pass the URL as first argument to this script or define"
   echo "one of the environment variable APPVEYOR_REPO_NAME (as owner/repo)"
   exit /b 1
)

if %argC% gtr 1 (
   set git_branch=%2
) else if not [%APPVEYOR_PULL_REQUEST_HEAD_REPO_BRANCH%] == [] (
   set git_branch=%APPVEYOR_PULL_REQUEST_HEAD_REPO_BRANCH%
) else if not [%APPVEYOR_REPO_BRANCH%] == [] (
   set git_branch=%APPVEYOR_REPO_BRANCH%
) else (
   echo "No testing branch specified, assuming master."
   echo "Note: You can define the environment variable APPVEYOR_REPO_BRANCH to set the branch."
   set git_branch="master"
)

set python_so_path=C:\msys64\mingw64\bin\libboost_python3-mt.dll
set python_executable=C:\msys64\mingw64\bin\python3.exe
set cmake_executable=C:\msys64\mingw64\bin\cmake.exe
set ctest_executable=C:\msys64\mingw64\bin\ctest.exe

%cmake_executable% ^
   -G Ninja ^
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
