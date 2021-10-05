:: Launch a python script using the docker image

@echo off
set "GUI=0"
set "ROMSPATH="
set "PYTHONFILE="
set "VOLUME="
set "ENVDISPLAYIP="
set "XSRVPATH="
set "CURDIR="
set "CMDTOEXEC="
 
SetLocal EnableDelayedExpansion

cls

if "%~1"=="" (
  echo ERROR. No arguments found
  goto errorArg
)
goto skipErrorArg
 :errorArg
echo Usage:
echo    - Headless: runDocker.bat "ROMSPATH=your\roms\local\path"
echo                              "PYTHONFILE=yourPythonScriptInCurrentDir.py"
echo                              "VOLUME=yourVolumeName" (optional)
echo.
echo    - With GUI: runDocker.bat "ROMSPATH=your\roms\local\path" 
echo                              "PYTHONFILE=yourPythonScriptInCurrentDir.py"
echo                              "GUI=1" 
echo                              "ENVDISPLAYIP=<vEthernetIP>:0.0"
echo                              "XSRVPATH=<pathToVcXsrv>"  (optional)
echo                              "VOLUME=yourVolumeName" (optional)
echo.
echo        Where: ENVDISPLAYIP is the IP address of the vEthernet, retrieve it with 'ipconfig' command
echo               XSRVPATH is the path to Windows VcXsrv X Server, usually located in 'C:\Program Files\vcxsrv.exe' 
echo.
echo    - Terminal: runDocker.bat "CMDTOEXEC=bash"
echo                              "VOLUME=yourVolumrName" (optional)
goto end
 :skipErrorArg

set %1
if not "%~2"=="" set %2
if not "%~3"=="" set %3
if not "%~4"=="" set %4
if not "%~5"=="" set %5
if not "%~6"=="" set %6

echo DIAMBRAROMSPATH ENV VAR = %DIAMBRAROMSPATH%
if NOT "%DIAMBRAROMSPATH%"=="" if "%ROMSPATH%"=="" set "ROMSPATH=%DIAMBRAROMSPATH%"

if "%PYTHONFILE%"=="" IF "%CMDTOEXEC%"=="" (
  echo ERROR. Either PYTHONFILE or CMDTOEXEC arguments must be provided when launching the run command
  goto errorArg
)
if "%GUI%"=="1" IF "%ENVDISPLAYIP%"=="" (
  echo ERROR. When running with GUI active, ENVDISPLAYIP arugment must be provided
  goto errorArg
)
if NOT "%PYTHONFILE%"=="" IF "%CMDTOEXEC%"=="" set "CMDTOEXEC=python %PYTHONFILE%"

set "CURDIR="%cd%""

echo.
echo Executing in the docker (CPU image):
echo   Roms path: %ROMSPATH%
echo   GUI Active: %GUI%
if "%GUI%"=="1" echo   XServer Display IP = %ENVDISPLAYIP%
if "%GUI%"=="1" echo   XServer Path = %XSRVPATH%
echo   Command: %CMDTOEXEC%
echo   Current Directory: %CURDIR%
echo   Volume: %VOLUME%
echo --
echo.

:: Process variables to prepare command
if NOT "%ROMSPATH%"=="" set ROMSPATH=--mount src=%ROMSPATH%,target="/opt/diambraArena/roms",type=bind
if NOT "%VOLUME%"=="" set VOLUME=-v %VOLUME%:/usr/local/lib/python3.6/dist-packages/

if "%GUI%"=="0" (
  set "CMDTOEXEC=xvfb-run !CMDTOEXEC!"
  docker run -it --rm --privileged %ROMSPATH% %VOLUME% ^
   --mount src=%CURDIR%,target="/opt/diambraArena/code",type=bind ^
   --name diambraArena diambra:diambra-arena-base ^
   sh -c "cd /opt/diambraArena/code/ && !CMDTOEXEC!" 
) else (
  rem VcXsrv options https://gist.github.com/ctaggart/68ead4d0d942b240061086f4ba587f5f

  if "%XSRVPATH%"=="" (

    echo Trying to retrieve XSRVPATH automatically ...
    set "XSRVPATH="
    FOR /F "tokens=* USEBACKQ" %%F IN (`WHERE /R C:\ VcXsrv.exe`) DO (
      SET "XSRVPATH=%%F"
    )

    if "!XSRVPATH!"=="" (
      echo "ERROR. Unable to retrieve XSRVPATH."
      echo "Have you installed Windows VcXsrv X Server (https://sourceforge.net/projects/vcxsrv/)?"
      goto end
    )
    echo XSRVPATH found in !XSRVPATH!  
  )

  echo Running Virtual X Server ...
  START /B CMD /C CALL "!XSRVPATH!" -noprimary -nowgl -ac -displayfd 664 -screen 0 400x300@1
  echo Running DIAMBRA Arena docker container ...
  docker run -it --rm --privileged -e DISPLAY="%ENVDISPLAYIP%" %ROMSPATH% %VOLUME% ^
   --mount src=%CURDIR%,target="/opt/diambraArena/code",type=bind ^
   --name diambraArena diambra:diambra-arena-base ^
   sh -c "cd /opt/diambraArena/code/ && %CMDTOEXEC%"
  TASKKILL /IM vcxsrv.exe /F
)
 :end
