:: Launch a python script using the docker image

@echo off
set "ROMSPATH="
set "PYTHONFILE="
set "GUI="
set "CURDIR="

if "%~1"=="" goto noArg
if "%~2"=="" goto noArg
if "%~3"=="" if "%DIAMBRAROMSPATH%"=="" goto noArg
goto skipNoArg
 :noArg
echo "ERROR: 3 parameters are required or 2 parameters + DIAMBRAROMSPATH Env variable set. Usage: runDocker.bat "ROMSPATH=your\roms\path" "PYTHONFILE=yourFile.py" "GUI=guiFlag""
goto end
 :skipNoArg

set %1
set %2
if not "%~3"=="" set %3

echo DIAMBRAROMSPATH ENV VAR = %DIAMBRAROMSPATH%
if NOT "%DIAMBRAROMSPATH%"=="" if "%ROMSPATH%"=="" set "ROMSPATH=%DIAMBRAROMSPATH%"

if "%ROMSPATH%"=="" goto missingPar
if "%PYTHONFILE%"=="" goto missingPar
if "%GUI%"=="" goto missingPar
goto skipMissingPar
 :missingPar
echo "ERROR: Some parameters are missing. Usage: runDocker.bat "ROMSPATH=your\roms\path" "PYTHONFILE=yourFile.py" "GUI=guiFlag""
echo ROMSPATH: %ROMSPATH%
echo PYTHONFILE: %PYTHONFILE%
echo GUI: %GUI%
goto end
 :skipMissingPar

echo.
echo Executing in the docker (CPU image):
echo   Roms path: %ROMSPATH%
echo   GUI Active: %GUI%
echo   Command: python %PYTHONFILE%
echo --
echo.

set "CURDIR="%cd%""

if "%GUI%"=="0" (
::#-v pythonDep:/usr/local/lib/python3.6/dist-packages/ \
 docker run -it --rm --privileged --mount src=%ROMSPATH%,target="/opt/diambraArena/roms",type=bind --mount src=%CURDIR%,target="/opt/diambraArena/code",type=bind --name diambraArena diambra:diambra-arena-base bash -c "cd /opt/diambraArena/code/ && python %PYTHONFILE%"
) else (
echo GUI 1
)
 :end
