@echo off
set "MY_DIR=%~dp0"
if "%MY_DIR:~-1%"=="\" set "MY_DIR=%MY_DIR:~0,-1%"

for /f "tokens=3" %%i in ('wsl ip route show default ^| findstr default') do set "HOST_IP=%%i"

if "%HOST_IP%"=="" set "HOST_IP=172.17.0.1"

:: Converts path
for /f "delims=" %%i in ('wsl wslpath "%MY_DIR%"') do set "WSL_PATH=%%i"

:: Ensures folder name matches (Check if 'PythonScripts' or 'pythonscripts')
set "PYTHON_SCRIPT=PythonScripts/cmpfourhundred_manual_control.py"

echo Launching Client...
echo Host IP: %HOST_IP%
echo Linux Path: %WSL_PATH%

:: Get the actual WSL username dynamically
for /f "delims=" %%i in ('wsl -d Ubuntu bash -c "whoami"') do set "WSL_USER=%%i"
echo WSL User: %WSL_USER%

:: Pre-create carlaCache structure and /home/CarlaUnreal which CARLA traverses to via ../../..
:: All done as root so no sudo password prompt is needed from the user
wsl -d Ubuntu -u root bash -c "mkdir -p /home/%WSL_USER%/carlaCache/0.10.0 && mkdir -p /home/CarlaUnreal && chown -R %WSL_USER%:%WSL_USER% /home/%WSL_USER%/carlaCache && chown -R %WSL_USER%:%WSL_USER% /home/CarlaUnreal && chmod -R 777 /home/%WSL_USER%/carlaCache && chmod -R 777 /home/CarlaUnreal"

::Execution Logic, kinda confusing ngl, but it works:
:: -Navigate to the project folder
:: -activate the tf_gpu environment
:: -Run the Python script
:: -Keep the terminal open with 'exec bash' 
:: throws away the output of print
start /high wsl -d Ubuntu bash -c "cd \"%WSL_PATH%\" && source ~/tf_gpu/bin/activate && python3 %PYTHON_SCRIPT% --host %HOST_IP%; exec bash"
exit