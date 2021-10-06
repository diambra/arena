#!/bin/bash
# Launch a python script using the docker image

function usage() {

  echo "Usage:"
  echo " "
  echo "  ./runDocker.sh [OPTIONS]"
  echo " "
  echo "OPTIONS:"
  echo "  -h Prints out this help message."
  echo " "
  echo "  -r \"<path>\" Specify your local path to where game roms are located."
  echo "              (Mandatory to run environments.)"
  echo " "
  echo "  -s <file> Python script to run inside docker container."
  echo "            Must be located in the folder from where the bash script is executed."
  echo " "
  echo "  -c <command> Command to be executed at docker container startup."
  echo "               Can be used to start and interactive linux shell, for example to install pip packages."
  echo " "
  echo "  -g <X> Specify if to run in Headless mode (X=0, default) or with GUI support (X=1)"
  echo " "
  echo "  -d <DEVICE> Specify if to run CPU docker image (DEVICE=CPU, default)"
  echo "              or the one with NVIDIA GPU Support (DEVICE=GPU)" 
  echo "              Requires Nvidia-Docker Toolkit installed"
  echo " " 
  echo "  -v <name> Specify the name of the volume where to store pip packages"
  echo "            installed inside the container to make them persistent. (Optional)"
  echo " " 
  echo "Examples:"
  echo "  - Headless (CPU): ./runDocker.sh -r \"your/roms/local/path\""
  echo "                                   -s yourPythonScriptInCurrentDir.py"
  echo "                                   -v yourVolumeName (optional)"
  echo " "      
  echo "  - Headless (GPU): ./runDocker.sh -r \"your/roms/local/path\""
  echo "                                   -s yourPythonScriptInCurrentDir.py"
  echo "                                   -d GPU"
  echo "                                   -v yourVolumeName (optional)"
  echo " "
  echo "  - With GUI (CPU): ./runDocker.sh -r \"your/roms/local/path\""
  echo "                                   -s yourPythonScriptInCurrentDir.py"
  echo "                                   -g 1"
  echo "                                   -v yourVolumeName (optional)"
  echo " "
  echo "  - Terminal (CPU): ./runDocker.sh -c bash"
  echo "                                   -v yourVolumeName (optional)"
  echo " "
}

clear

device="CPU"
gui="0"
romsPath=""
pythonFile=""
cmd=""
gpuSetup=""
volume=""

while getopts r:s:d:g:c:v:h flag
do
    case "${flag}" in
        r) romsPath=${OPTARG};;
        s) pythonFile=${OPTARG};;
        d) device=${OPTARG};;
        g) gui=${OPTARG};;
        c) cmd=${OPTARG};;
        v) volume="-v ${OPTARG}:/usr/local/lib/python3.6/dist-packages/";;
        h) usage; exit 0;;
    esac
done

# Check inputs/variables
if [ -z "$DIAMBRAROMSPATH" ]
then
  :
else
  if [ -z "$romsPath" ]
  then
      romsPath=$DIAMBRAROMSPATH
  else
    if [ "$romsPath" != "$DIAMBRAROMSPATH" ]
    then
        echo "WARNING \$DIAMBRAROMSPATH and \$romsPath differ: \"$DIAMBRAROMSPATH\" VS \"$romsPath\", using \"$romsPath\""
    fi
  fi
fi

if [ "$gui" == "1" ]
then
  if [ "$device" == "GPU" ]
  then 
      echo "WARNING GUI can be used only with CPU docker image, running headless."
      gui="0"
  fi
fi

if [ -z "$cmd" ]
then
  if [ -z "$pythonFile" ]
  then
      echo "ERROR: use etither \"-s\" to execute a python script or \"-c\" to execute a command"
      usage
      exit 1
  else
      cmd="python $pythonFile"
  fi
else
  if [ -z "$pythonFile" ]
  then
      :
  else
      echo "WARNING: both \"-c\" and \"-s\" arguments passed, using \"-c\": $cmd"
  fi
fi

if [ "$device" == "GPU" ]
then
    # Check if nvidia-docker is installed 
    nvidiaDockerCheck=$(dpkg-query -W -f='${Status} ${Version}\n' nvidia-docker2)
    if [[ "$nvidiaDockerCheck" == "install ok installed"* ]]; then
      echo "Nvidia-Docker package found."
    else
      echo "WARNING: Nvidia-Docker package has not been found, container with GPU support will likely abort."
      echo "Make sure to install the Nvidia-Docker package following this guide:"
      echo "  https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
    fi

    gpuSetup="--gpus all"
    imageName="diambra:diambra-arena-gpu-cuda10.0"
else
    device="CPU"
    imageName="diambra:diambra-arena-base"
fi

echo " "
echo "Executing in the docker ($device image):";
echo "  Roms path: $romsPath";
echo "  Device: $device";
echo "  GUI Active: $gui";
echo "  Command: $cmd";
echo "  Volumes option: $volume";
echo "---"
echo " "

if [ "$romsPath" != "" ]
then 
  romsPath="--mount src=$romsPath,target="/opt/diambraArena/roms",type=bind "
fi

if [ "$gui" == "0" ]
then
    cmd="xvfb-run $cmd"
    docker run -it --rm $gpuSetup --privileged $volume $romsPath \
     --mount src=$(pwd),target="/opt/diambraArena/code",type=bind \
     --name diambraArena $imageName \
      sh -c "cd /opt/diambraArena/code/ && $cmd"
else
    ./x11docker --cap-default --hostipc --network=host --name=diambraArena --wm=host \
     --pulseaudio --size=1024x600 -- $gpuSetup --privileged $volume $romsPath \
     --mount src=$(pwd),target="/opt/diambraArena/code",type=bind \
     -- $imageName &>/dev/null & sleep 4s; \
      docker exec -u 0 --privileged -it diambraArena \
      sh -c "set -m; cd /opt/diambraArena/code/ && $cmd"; pkill -f "bash ./x11docker*"
      #sh -c "set -m; cd /opt/diambraArena/code/ && $cmd & sleep 10s; wmctrl -r "MAME" -e 0,307,150,400,300; fg"; pkill -f "bash ./x11docker*"
fi
