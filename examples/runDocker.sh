#!/bin/bash
# Launch a python script using the docker image
# runDocker.sh -r "/home/apalmas/Applications/Diambra/diambraEngine/roms/mame/" -s diambraArenaGist.py -d GPU

device="CPU"
gui="0"
romsPath=""
pythonFile=""
cmd=""
gpuSetup=""
volume=""

while getopts r:s:d:g:c:v: flag
do
    case "${flag}" in
        r) romsPath=${OPTARG};;
        s) pythonFile=${OPTARG};;
        d) device=${OPTARG};;
        g) gui=${OPTARG};;
        c) cmd=${OPTARG};;
        v) volume="-v ${OPTARG}:/usr/local/lib/python3.6/dist-packages/";;
    esac
done

# Check inputs/variables
if [ -z "$DIAMBRAROMSPATH" ]
then
  if [ -z "$romsPath" ]
  then
      echo "ERROR: \$DIAMBRAROMSPATH Environment variable is empty. Either add the absolute path to roms in your environment variables or provide it as input argument with the \"-c\" flag"
      exit 1
  fi
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

if [ "$gui" == "0" ]
then
    docker run -it --rm $gpuSetup --privileged $volume \
     --mount src=$romsPath,target="/opt/diambraArena/roms",type=bind \
     --mount src=$(pwd),target="/opt/diambraArena/code",type=bind \
     --name diambraArena $imageName \
      sh -c "cd /opt/diambraArena/code/ && $cmd"
else
    ./x11docker --cap-default --hostipc --network=host --name=diambraArena --wm=host \
     --pulseaudio --size=1024x600 -- $gpuSetup --privileged $volume \
     --mount src=$romsPath,target="/opt/diambraArena/roms",type=bind \
     --mount src=$(pwd),target="/opt/diambraArena/code",type=bind \
     -- $imageName &>/dev/null & sleep 4s; \
      docker exec -u 0 --privileged -it diambraArena \
      sh -c "set -m; cd /opt/diambraArena/code/ && $cmd"; pkill -f "bash ./x11docker*"
      #sh -c "set -m; cd /opt/diambraArena/code/ && $cmd & sleep 10s; wmctrl -r "MAME" -e 0,307,150,400,300; fg"; pkill -f "bash ./x11docker*"
fi
