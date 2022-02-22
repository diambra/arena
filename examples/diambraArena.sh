#!/bin/bash
# Launch a python script using the docker image

osName=$(uname -s)
DOCKER=${DOCKER:-docker}
X11DOCKER=${X11DOCKER:-./x11docker}

function usage() {

  echo -e "\033[1mUsage:\033[0m"
  echo " "
  echo "  ./diambraArena.sh [OPTIONS]"
  echo " "
  echo -e "\033[1mOPTIONS:\033[0m"
  echo "  -h Prints out this help message."
  echo " "
  echo "  -l Prints out available games list."
  echo " "
  echo "  -t <romFile.zip> Checks ROM file validity."
  echo " "
  echo "  -r \"<path>\" Specify your local path to where game roms are located."
  echo "              (Mandatory to run environments and to check ROM validity.)"
  echo " "
  echo "  -s <file> Python script to run inside docker container."
  echo "            Must be located in the folder from where the bash script is executed."
  echo " "
  echo "  -c <command> Command to be executed at docker container startup."
  echo "               Can be used to start and interactive linux shell, for example to install pip packages."
  echo " "
  echo "  -g <X> Specify if to run in Headless mode (X=0, default) or with GUI support (X=1)"
  echo " "
  if [ $osName == "Linux" ]
  then
    echo "  -d <DEVICE> Specify if to run CPU docker image (DEVICE=CPU, default)"
    echo "              or the one with NVIDIA GPU Support (DEVICE=GPU)" 
    echo "              Requires Nvidia-Docker Toolkit installed"
    echo " " 
  else
    envDisplayIp=$(ifconfig en0 | awk '/inet /&&!/127.0.0.1/{print $2}')
    echo "  -e <vEthernetIP>:0.0 Specify the vEthernet IP Address on which the Virtual X Server is listening."
    echo "                       The address can be retrieved using 'ifconfig en0' command."
    echo "                       (Optional, the script will use $vEthIp (automatically recovered)"
    echo "                       for executions with GUI support. If it's not correct, please provide it with this option.)"
    echo " " 
  fi
  echo "  -v <name> Specify the name of the volume where to store pip packages"
  echo "            installed inside the container to make them persistent. (Optional)"
  echo " " 
  echo -e "\033[1mExamples:\033[0m"
  echo "  - Availble games list with details: ./diambraArena.sh -l"
  echo " "
  echo "  - ROM File Validation: ./diambraArena.sh -r \"your/roms/local/path\""
  echo "                                           -t romFile.zip"
  echo " "
  echo "  - Headless (CPU): ./diambraArena.sh -r \"your/roms/local/path\""
  echo "                                      -s yourPythonScriptInCurrentDir.py"
  echo "                                      -v yourVolumeName (optional)"
  echo " "      
  if [ $osName == "Linux" ]
  then
    echo "  - Headless (GPU): ./diambraArena.sh -r \"your/roms/local/path\""
    echo "                                      -s yourPythonScriptInCurrentDir.py"
    echo "                                      -d GPU"
    echo "                                      -v yourVolumeName (optional)"
    echo " "
  fi
  echo "  - With GUI (CPU): ./diambraArena.sh -r \"your/roms/local/path\""
  echo "                                      -s yourPythonScriptInCurrentDir.py"
  echo "                                      -g 1"
  if [ $osName != "Linux" ] 
  then
    echo "                                      -e <vEthernetIP>:0.0 (optional, default=$vEthIp)"
  fi
  echo "                                      -v yourVolumeName (optional)"
  echo " "
  echo "  - Terminal (CPU): ./diambraArena.sh -c bash"
  echo "                                      -v yourVolumeName (optional)"
  echo " "
  if [ $osName == "Linux" ]
  then
    echo "  - CUDA Installation Test (GPU): ./diambraArena.sh -c \"cat /proc/driver/nvidia/version; nvcc -V\""
    echo "                                                    -d GPU"
  fi
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
envDisplayIp=""
romFile=""

while getopts r:s:d:g:c:v:e:ht:l flag
do
    case "${flag}" in
        r) romsPath=${OPTARG};;
        s) pythonFile=${OPTARG};;
        d) device=${OPTARG};;
        g) gui=${OPTARG};;
        c) cmd=${OPTARG};;
        v) volume="-v ${OPTARG}:/usr/local/lib/python3.6/dist-packages/";;
        e) envDisplayIp=${OPTARG};;
        h) usage; exit 0;;
        t) romFile=${OPTARG}; cmd="python -c \"import diambraArena, os; diambraArena.checkGameSha256(os.path.join(os.getenv('DIAMBRAROMSPATH'), '$romFile'))\"";;
        l) cmd="python -c \"import diambraArena; diambraArena.availableGames(True, True)\"";;
    esac
done

# Check inputs/variables
if [ $osName != "Linux" ]
then
  if [ $device == "GPU" ]
  then
    echo "WARNING: No GPU support for macOS. Forcing CPU Docker image execution."
    device="CPU"
  fi
fi

if [ "$DIAMBRAROMSPATH" != "" ]
then
  if [ -z "$romsPath" ]
  then
      romsPath=$DIAMBRAROMSPATH
  else
    if [ "$romsPath" != "$DIAMBRAROMSPATH" ]
    then
        echo "WARNING: \$DIAMBRAROMSPATH and \$romsPath differ: \"$DIAMBRAROMSPATH\" VS \"$romsPath\", using \"$romsPath\""
    fi
  fi
fi

if [ "$gui" == "1" ]
then
  if [ "$device" == "GPU" ]
  then 
      echo "WARNING: GUI can be used only with CPU docker image, running headless."
      gui="0"
  fi
  if [ $osName != "Linux" ]
  then 
    if [ "$envDisplayIp" == "" ]
    then
      echo "Trying to retrieve ENVDISPLAYIP automatically ..."
      envDisplayIp=$(ifconfig en0 | awk '/inet /&&!/127.0.0.1/{print $2}')

      if [ "$envDisplayIp" == "" ]
        then
        echo "ERROR: Unable to retrieve ENVDISPLAYIP, provide it a command line argument."
        usage
        exit 1
      fi
 
      echo "ENVDISPLAYIP found in $envDisplayIp"
   
    fi
  fi
fi

if [ -z "$cmd" ]
then
  if [ -z "$pythonFile" ]
  then
      echo "ERROR: No command to execute found. Use etither \"-s\" to execute a python script or \"-c\" to execute a command"
      usage
      exit 1
  else
      cmd="python $pythonFile"
  fi
else
  if [ "$pythonFile" != "" ]
  then
      echo "WARNING: Both \"-c\" and \"-s\" arguments passed, using \"-c\": $cmd"
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
    imageName="diambra/diambra-arena:gpu-cuda10.0"
else
    device="CPU"
    imageName="diambra/diambra-arena:base"
fi

echo " "
echo "Executing in the docker ($device image):"
echo "  OS: $osName"
echo "  Roms path: $romsPath"
echo "  Device: $device"
echo "  GUI Active: $gui"
echo "  Command: $cmd"
echo "  Volumes option: $volume"
echo "---"
echo " "

if [ "$romsPath" != "" ]
then 
  romsPath="--mount src=$romsPath,target="/opt/diambraArena/roms",type=bind "
fi

if [ "$gui" == "0" ]
then
    cmd="xvfb-run $cmd"
    $DOCKER run -it --rm $gpuSetup --privileged $volume $romsPath \
     --mount src=$(pwd),target="/opt/diambraArena/code",type=bind \
     -v diambraService:/root/ --name diambraArena $imageName \
      sh -c "cd /opt/diambraArena/code/ && $cmd"
else
  if [ $osName == "Linux" ]
  then
    $X11DOCKER --cap-default --hostipc --network=host --name=diambraArena --wm=host \
     --pulseaudio --size=1024x600 -- $gpuSetup --privileged $volume $romsPath \
     --mount src=$(pwd),target="/opt/diambraArena/code",type=bind \
     -v diambraService:/root/ -- $imageName &>/dev/null & sleep 10s; \
      $DOCKER exec -u 0 --privileged -it diambraArena \
      sh -c "set -m; cd /opt/diambraArena/code/ && $cmd"; pkill -f "bash ./x11docker*"
      #sh -c "set -m; cd /opt/diambraArena/code/ && $cmd & sleep 10s; wmctrl -r "MAME" -e 0,307,150,400,300; fg"; pkill -f "bash ./x11docker*"
  else
    echo "Boot phase will require about 30 seconds, please be patient..."
    echo "Running Virtual X Server ..."
    # https://www.xquartz.org/releases/XQuartz-2.7.8.html
    socat TCP-LISTEN:6000,reuseaddr,fork UNIX-CLIENT:\"$DISPLAY\" &>/dev/null & sleep 15s; open -a xquartz; sleep 5s; \
    echo "Running DIAMBRA Arena docker container ..."; \
    $DOCKER run -it --rm $gpuSetup --privileged -e DISPLAY="$envDisplayIp:0.0" $volume $romsPath \
     --mount src=$(pwd),target="/opt/diambraArena/code",type=bind \
     -v diambraService:/root/ --name diambraArena $imageName \
      sh -c "cd /opt/diambraArena/code/ && $cmd"
    # TODO: KILLARE QUARTZ?
  fi
fi
