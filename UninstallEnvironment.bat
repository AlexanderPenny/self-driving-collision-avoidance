@echo off
echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
echo WARNING: This will delete the Ubuntu WSL instance
echo and all files saved inside it (including tf_gpu).
echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

:: Confirmation to prevent accidental deletion
set /p confirm="Are you sure you want to uninstall? It is suggested to wait until after you have submitted the survey (Y/N): "
if /i "%confirm%" neq "Y" (
    echo Uninstall cancelled.
    pause
    exit
) 

:: Removes the Linux Environment
echo Unregistering Ubuntu WSL Distro...
wsl --unregister Ubuntu 
echo [OK] Ubuntu instance removed.

:: Removes firewall rules
echo Removing firewall rules...
netsh advfirewall firewall delete rule name="CARLA Traffic Manager"
netsh advfirewall firewall delete rule name="CARLA Main"
echo [OK] Firewall rules removed.

echo ====================================================
echo CLEANUP COMPLETE.
echo The environment has been reset.
echo ====================================================
pause