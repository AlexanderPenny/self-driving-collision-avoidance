@echo off
set CARLA_PATH="packagedCarlaUnrealProject\CarlaUnreal.exe"

echo Launching CARLA Server...

start "" %CARLA_PATH% RuralMap0 -server -log

echo CARLA Unreal Engine 5 is now running as a server. 
echo You can now run StartClient.bat to connect the client and start the simulation.
echo After starting StartClient.bat, press "Tab" once and then "Shift + L" to enable the high beams (necessary for the simulation).
echo Press any key to exit this window once you have started the client...
exit
pause