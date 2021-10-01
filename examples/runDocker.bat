:: Launch a python script using the docker image
:: No GUI Run
:: runDocker.bat "ROMSPATH=your\roms\path" "PYTHONFILE=yourFile.py" "GUI=guiFlag"
:: GUI Run

@echo off
set "ROMSPATH="
set "PYTHONFILE="
set "GUI=0"
set "ENVDISPLAYIP="
set "XSRVPATH="
set "CURDIR="

if "%~1"=="" goto noArg
if "%~2"=="" goto noArg
if "%~3"=="" if "%DIAMBRAROMSPATH%"=="" goto noArg
goto skipNoArg
 :noArg
echo "ERROR: A minimum of 2 parameters are required."
echo " Usage:"
echo "    - Headless: runDocker.bat "ROMSPATH=your\roms\path" "PYTHONFILE=yourFile.py" "
echo "    - With GUI: runDocker.bat "ROMSPATH=your\roms\path" "PYTHONFILE=yourFile.py" "GUI=1" "ENVDISPLAYIP=<vEthernetIP>:0.0" (optional)"XSRVPATH=<pathToVcXsrv>" "
echo "      Where: ENVDISPLAYIP is the IP address of the vEthernet, retrieve it with 'ipconfig' command"
echo "             XSRVPATH is the path to Windows VcXsrv X Server, usually located in 'C:\Program Files\vcxsrv.exe' "
        
goto end
 :skipNoArg

set %1
set %2
if not "%~3"=="" set %3

echo DIAMBRAROMSPATH ENV VAR = %DIAMBRAROMSPATH%
if NOT "%DIAMBRAROMSPATH%"=="" if "%ROMSPATH%"=="" set "ROMSPATH=%DIAMBRAROMSPATH%"

if "%ROMSPATH%"=="" goto missingPar
if "%PYTHONFILE%"=="" goto missingPar
if %GUI==1% IF "%ENVDISPLAYIP%"=="" goto missingPar
goto skipMissingPar
 :missingPar
echo "ERROR: Some parameters are missing."
echo "Usage: runDocker.bat "ROMSPATH=your\roms\path" "PYTHONFILE=yourFile.py" "GUI=guiFlag""
echo ROMSPATH: %ROMSPATH%
echo PYTHONFILE: %PYTHONFILE%
echo GUI: %GUI%
if %GUI==1% echo ENVDISPLAYIP: %ENVDISPLAYIP%
goto end
 :skipMissingPar

set "CURDIR="%cd%""

echo.
echo Executing in the docker (CPU image):
echo   Roms path: %ROMSPATH%
echo   GUI Active: %GUI%
echo   Command: python %PYTHONFILE%
echo   Current Directory: %CURDIR%
echo --
echo.

if "%GUI%"=="0" (
  ::#-v pythonDep:/usr/local/lib/python3.6/dist-packages/ \
  docker run -it --rm --privileged --mount src=%ROMSPATH%,target="/opt/diambraArena/roms",type=bind --mount src=%CURDIR%,target="/opt/diambraArena/code",type=bind --name diambraArena diambra:diambra-arena-base sh -c "cd /opt/diambraArena/code/ && python %PYTHONFILE%" 
) else (
  rem VcXsrv options https://gist.github.com/ctaggart/68ead4d0d942b240061086f4ba587f5f
  rem vcxsrv.exe -noprimary -nowgl -ac -displayfd 664 -screen 0 400x300@1
  rem WHERE /R C: VcXsrv.exe

  FOR /F "tokens=* USEBACKQ" %%F IN (`WHERE /R C:\ VcXsrv.exe`) DO (
    SET XSRVPATH=%%F
  )

  echo XSRVPATH=%XSRVPATH%

  docker run -it --rm --privileged -e DISPLAY="%ENVDISPLAY%" --mount src=%ROMSPATH%,target="/opt/diambraArena/roms",type=bind --mount src=%CURDIR%,target="/opt/diambraArena/code",type=bind --name diambraArena diambra:diambra-arena-base sh -c "cd /opt/diambraArena/code/ && python %PYTHONFILE%"
)
 :end
