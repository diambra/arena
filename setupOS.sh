#!/bin/bash

stable_baselines=0
help=0

function help()
{
    echo "DIAMBRA Environment Helper"
    echo "No flags: => core installation"
    echo "Flag -c | --core => core installation"
    echo "Flag -s | --stable-baselines => stable-baselines installation"
    echo "Flag -h | --help => print this page"
}

while (( "$#" )); do
    case "$1" in 
        -c|--core)
        shift
        ;;
        -s|--stable-baselines)
        stable_baselines=1
        shift
        ;;
        -h|--help)
        help=1
        shift
        ;;
    esac
done

if [ $help -eq 1 ]; then
    help
    exit 100
fi

function setupMintUlyssa() {
    echo 'Updating APT'
    sudo apt-get update

    if [ $stable_baselines -eq 1 ]; then
        sudo apt-get install cmake libopenmpi-dev python3-dev zlib1g-dev 
    fi
    sudo apt-get install libboost1.71-dev libboost-system1.71-dev libboost-filesystem1.71-dev qt5-default libssl-dev libsdl2-ttf-dev xvfb python3-pip
}

function setupMintTessa() {
    echo 'Updating APT'
    sudo apt-get update

    if [ $stable_baselines -eq 1 ]; then
        sudo apt-get install cmake libopenmpi-dev python3-dev zlib1g-dev 
    fi
    sudo apt-get install libboost1.65-dev qt5-default libssl-dev libsdl2-ttf-dev xvfb python3-pip
}

function setupUbuntuGroovyGorilla() {
    echo 'Updating APT'
    sudo apt-get update

    if [ $stable_baselines -eq 1 ]; then
        sudo apt-get install cmake libopenmpi-dev python3-dev zlib1g-dev 
    fi 
    sudo apt-get install libboost1.71-dev libboost-system1.71-dev libboost-filesystem1.71-dev qt5-default libssl-dev libsdl2-ttf-dev xvfb python3-pip
}

function setupUbuntuBionicBeaver() {
    echo 'Updating APT'
    sudo apt-get update

    if [ $stable_baselines -eq 1 ]; then
        sudo apt-get install cmake libopenmpi-dev python3-dev zlib1g-dev 
    fi
    sudo apt-get install libboost1.65-dev qt5-default libssl-dev libsdl2-ttf-dev xvfb python3-pip
}

distroName=$(cat /etc/*-release | uniq -u | grep DISTRIB_ID)
distroRelease=$(cat /etc/*-release | uniq -u | grep DISTRIB_RELEASE)
IFS='='
read -ra array <<< "$distroName"
distroName=${array[1]}
read -ra array <<< "$distroRelease"
distroRelease=${array[1]}

if [ $distroName == "LinuxMint" ]; then
	isUlyssa=$(echo $distroRelease" > 20" | bc)
	isTessa=$(echo $distroRelease" >= 19" | bc)
	if [ $isUlyssa -eq 1 ]; then
		echo "Mint Ulyssa Detected"
        	setupMintUlyssa
	elif [ $isTessa -eq 1 ]; then
		echo "Mint Tessa Detected"
        	setupMintTessa
	else
		echo "Mint version not supported"
	fi
fi

if [ $distroName == "Ubuntu" ]; then
	isAtLeastGorilla=$(echo $distroRelease" > 20" | bc)
	isAtLeastBionicBeaver=$(echo $distroRelease" > 18" | bc)
	if [ $isAtLeastGorilla -eq 1 ]; then
		echo "Ubuntu Groovy Gorilla Detected"
        setupUbuntuGroovyGorilla
	elif [ $isAtLeastBionicBeaver -eq 1 ]; then
		echo "Ubuntu Bionic Beaver Detected"
        setupUbuntuBionicBeaver
    else
		echo "Ubuntu version not supported"
	fi
fi

