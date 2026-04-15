@echo off
echo ====================================================
echo Alexander Penny's Honours Project - Master Installer
echo ====================================================

:: Check for Admin
net session >nul 2>&1
if %errorLevel% neq 0 goto :NotAdmin

:: Set Paths 
set "CURRENT_DIR=%~dp0"
if "%CURRENT_DIR:~-1%"=="\" set "CURRENT_DIR=%CURRENT_DIR:~0,-1%"
set "VER_FILE=%CURRENT_DIR%\Depedencies\python_version.txt"

:: Get version from file
set "PY_VER=3.11"
if exist "%VER_FILE%" set /p PY_VER=<"%VER_FILE%"

:: [1/5] Ensuring WSL and Ubuntu are installed
echo [1/5] Ensuring WSL and Ubuntu are installed...
wsl --install -d Ubuntu

:: --- Verification Check ---
wsl -d Ubuntu echo "Connection Test" >nul 2>&1
if %errorlevel% neq 0 goto :WslError

echo [OK] WSL/Ubuntu status confirmed.

:: [2/5] Update and install Python version from file
echo [2/5] Installing Python %PY_VER% and system libraries...
wsl -d Ubuntu -u root bash -c "apt-get update && apt-get install -y software-properties-common && add-apt-repository -y ppa:deadsnakes/ppa && apt-get update"
wsl -d Ubuntu -u root apt-get install -y python%PY_VER% python%PY_VER%-venv python%PY_VER%-dev libpng16-16t64 libjpeg8 libtiff6

echo [3/5] Preparing Linux paths... 
for /f "delims=" %%i in ('wsl wslpath "%CURRENT_DIR%\Depedencies\requirements_c.txt"') do set "WSL_REQS=%%i"

:: [4/5] Create the virtual environment
echo [4/5] Creating 'tf_gpu' virtual environment (Python %PY_VER%)... 
wsl -d Ubuntu bash -c "python%PY_VER% -m venv ~/tf_gpu"
wsl -d Ubuntu bash -c "mkdir -p ~/carlaCache"
netsh advfirewall firewall add rule name="CARLA Traffic Manager" dir=in action=allow protocol=TCP localport=8000
netsh advfirewall firewall add rule name="CARLA Main" dir=in action=allow protocol=TCP localport=2000

:: [5/5] Install dependencies
echo [5/5] Installing Python dependencies...
wsl -d Ubuntu bash -c "source ~/tf_gpu/bin/activate && pip install --upgrade pip && pip install -r '%WSL_REQS%' && pip install --no-deps 'invertedai @ git+https://github.com/inverted-ai/invertedai.git@0a53610d8377620e79728ade1606259a75195f4d'"

echo ====================================================
echo INSTALLATION SUCCESSFUL (Using Python %PY_VER%).
echo ====================================================
pause
exit

:: ====================================================
:: ERROR HANDLERS (The script jumps here if something fails)
:: ====================================================

:NotAdmin
echo [ERROR] Please right-click this file and "Run as Administrator".
pause
exit

:WslError
echo [DETECTED] WSL is not responding or Virtualization is disabled.
echo Attempting to enable Virtual Machine Platform...
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
echo ----------------------------------------------------
echo [ACTION REQUIRED] BIOS VIRTUALIZATION NEEDED
echo ----------------------------------------------------
echo 1. REBOOT your computer now.
echo 2. During startup, enter BIOS (usually F2, F12, or DEL).
echo 3. Enable "Intel Virtualization Technology" or "AMD-V".
echo 4. Save and Exit, then run this installer again.
echo ----------------------------------------------------
pause
exit