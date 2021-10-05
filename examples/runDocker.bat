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
  goto usage
)
goto skipUsage
 :usage
echo Usage: 
echo.
echo    runDocker.bat [OPTIONS]
echo.
echo  OPTIONS:
echo    "ROMSPATH=<path>" Specify your local path to where game roms are located. 
echo                      (Mandatory to run environments.)
echo.
echo    "PYTHONFILE=<file>" Python script to run inside docker container. 
echo                        Must be located in the folder from where the batch script is executed.
echo.
echo    "CMDTOEXEC=<command>" Command to be executed at docker container startup.
echo                          Can be used to start and interactive linux shell, for example to install pip packages.
echo.
echo    "GUI=<X>" Specify if to run in Headless mode (X=0, default) or with GUI support (X=1)
echo.
echo    "ENVDISPLAYIP=<vEthernetIP>:0.0" Specify the vEthernet IP Address on which the Virtual X Server is listening. 
echo                                     The address can be retrieved using `ipconfig` command, 
echo                                     look for `Default Switch` or `WSL` in connection details.
echo                                     (Mandatory for executions with GUI support.)
echo. 
echo    "XSRVPATH=<path>" Specify where Windows X Server executable is located.
echo                      Standard location is usually `C:\Program Files\vcxsrv.exe`
echo                      (Optional, the script will try to recover it automatically.)
echo. 
echo    "VOLUME=<name>" Specify the name of the volume where to store pip packages 
echo                    installed inside the container to make them persistent. (Optional)
echo.
echo Examples:
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
echo    - Terminal: runDocker.bat "CMDTOEXEC=bash"
echo                              "VOLUME=yourVolumrName" (optional)
goto end
 :skipUsage

if %1 == "-h" goto :usage

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
  goto usage
)
if "%GUI%"=="1" IF "%ENVDISPLAYIP%"=="" (
  echo ERROR. When running with GUI active, ENVDISPLAYIP arugment must be provided
  goto usage
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
