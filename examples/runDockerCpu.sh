#!/bin/bash
# Launch a python script using the docker CPU image

while getopts r:c: flag
do
    case "${flag}" in
        r) romsPath=${OPTARG};;
        c) cmd_line=${OPTARG};;
    esac
done

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

echo "Executing in the docker (CPU image):"
echo "Roms path: $romsPath";
echo "Command: $cmd_line";

 #-v pythonDep:/usr/local/lib/python3.6/dist-packages/ \
docker run -it --rm --privileged \
 --mount src=$romsPath,target="/opt/diambraArena/roms",type=bind \
 --mount src=$(pwd),target="/opt/diambraArena/code",type=bind \
 --name diambraArena diambra:diambra-arena-base \
  bash -c "cd /opt/diambraArena/code/ && $cmd_line"
