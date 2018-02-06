rem C:\msys64\usr\bin\pacman -Ql mingw-w64-x86_64-python3
rem C:\msys64\usr\bin\pacman -Ql mingw-w64-x86_64-boost
C:\msys64\usr\bin\pacman --noconfirm -S mingw-w64-x86_64-cmake
C:\msys64\usr\bin\pacman --noconfirm -S mingw-w64-x86_64-python3
C:\msys64\usr\bin\pacman --noconfirm -S mingw-w64-x86_64-python3-pip
C:\msys64\usr\bin\pacman --noconfirm -S mingw-w64-x86_64-boost
C:\msys64\usr\bin\pacman --noconfirm -S mingw-w64-x86_64-ninja

C:\msys64\mingw64\bin\python3.exe "C:\msys64\mingw64\bin\pip3-script.py" install pyyaml

rem sphinx is only required to build the Leidokos-Python's API
rem C:\msys64\mingw64\bin\python3.exe "C:\msys64\mingw64\bin\pip3-script.py" install sphinx