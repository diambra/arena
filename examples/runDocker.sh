#!/bin/bash
# Launch a python script using the docker image

device="CPU"
gui="0"

while getopts r:s:d:g:c: flag
do
    case "${flag}" in
        r) romsPath=${OPTARG};;
        s) pythonFile=${OPTARG};;
        d) device=${OPTARG};;
        g) gui=${OPTARG};;
        c) cmd=${OPTARG};;
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
echo "---"
echo " "

if [ "$gui" == "0" ]
then
     #-v pythonDep:/usr/local/lib/python3.6/dist-packages/ \
    docker run -it --rm --gpus all --privileged \
     --mount src=$romsPath,target="/opt/diambraArena/roms",type=bind \
     --mount src=$(pwd),target="/opt/diambraArena/code",type=bind \
     --name diambraArena $imageName \
      bash -c "cd /opt/diambraArena/code/ && $cmd"
else
     #-v pythonDep:/usr/local/lib/python3.6/dist-packages/ \
    ./x11docker --cap-default --hostipc --network=host --name=diambraArena --wm=host --pulseaudio -- --gpus all --privileged \
     --mount src=$romsPath,target="/opt/diambraArena/roms",type=bind \
     --mount src=$(pwd),target="/opt/diambraArena/code",type=bind \
      -- $imageName &>/dev/null & sleep 4s; \
      docker exec -u 0 --privileged -it diambraArena \
      bash -c "cd /opt/diambraArena/code/ && $cmd"
fi

