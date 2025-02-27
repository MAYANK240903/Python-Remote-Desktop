@echo off
setlocal enabledelayedexpansion

:: Define the installation directory for a single user
set "install_dir=%LOCALAPPDATA%\Programs\Python\Python311"

if not exist %install_dir%\python.exe (

    :: Download python3.11.1

    :: Check if the Python installer exists in the current directory
    if not exist python-3.11*.exe (
        :: Download python3.11.1
        echo Python 3.11 installer not found in the current directory, Downloading Python 3.11.
        curl -OL https://www.python.org/ftp/python/3.11.1/python-3.11.1-amd64.exe
    )


    :: Get the Python installer filename (assuming only one Python installer)
    for %%f in (python-3.11*.exe) do set "installer=%%f"


    :: Install Python 3.11 silently for the CURRENT USER with pip, lib, and exe options
    echo Installing Python 3.11 for the current user...
    start /wait %installer% /simple
    :: InstallAllUsers=0 PrependPath=0 Include_pip=1 Include_test=0 TargetDir="%install_dir%"

    :: Check if Python was installed successfully
    if not exist "%install_dir%\python.exe" (
        echo Python installation failed.
        exit /b 1
    )
)

:: Add Python 3.11 to the user PATH permanently
echo Adding Python 3.11 to the user PATH permanently...

:: Get the current user PATH
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v Path') do set "current_path=%%b"

:: Check if Python is already in the PATH
echo %current_path% | find /i "%install_dir%" >nul
if errorlevel 1 (
    :: Append Python directory to the PATH
    setx PATH "%current_path%;%install_dir%"
    if errorlevel 1 (
        echo Failed to update the user PATH.
        exit /b 1
    )
) else (
    echo Python 3.11 is already in the user PATH.
)

:: Add Python Scripts directory to the user PATH permanently
echo Adding Python 3.11 Scripts directory to the user PATH permanently...

:: Get the current user PATH again
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v Path') do set "current_path=%%b"

:: Check if Python Scripts directory is already in the PATH
echo %current_path% | find /i "%install_dir%\Scripts" >nul
if errorlevel 1 (
    :: Append Python Scripts directory to the PATH
    setx PATH "%current_path%;%install_dir%\Scripts"
    if errorlevel 1 (
        echo Failed to update the user PATH with the Scripts directory.
        exit /b 1
    )
) else (
    echo Python 3.11 Scripts directory is already in the user PATH.
)

:: Install dependencies from requirements.txt using pip
if exist "requirements.txt" (
    echo Installing dependencies from requirements.txt...
    "%install_dir%\python311.exe" -m pip install --upgrade pip
    "%install_dir%\python311.exe" -m pip install -r requirements.txt
) else (
    echo requirements.txt not found.
    py -3.11 -m pip install screeninfo
    py -3.11 -m pip install opencv-python
    py -3.11 -m pip install tk
    py -3.11 -m pip install pynput
    py -3.11 -m pip install pyautogui
    py -3.11 -m pip install pyturbojpeg
    py -3.11 -m pip install bettercam
    py -3.11 -m pip install mss
    py -3.11 -m pip install numpy
)

echo Downloading PyTurboJPEG Libraries...
curl -OL https://github.com/libjpeg-turbo/libjpeg-turbo/releases/download/3.1.0/libjpeg-turbo-3.1.0-gcc64.exe
echo Download Complete!
echo Installing...
start /wait libjpeg-turbo-3.1.0-gcc64.exe
echo PyTurboJPEG Library Installed.

echo Installation complete.
endlocal