#!/bin/bash

function setupMintUlyssa() {
    echo 'Updating APT'
    sudo apt update
    sudo apt-get update

    sudo apt-get install cmake libopenmpi-dev python3-dev zlib1g-dev
    sudo apt-get install libboost1.71-dev libboost-system1.71-dev libboost-filesystem1.71-dev qt5-default libssl-dev libsdl2-ttf-dev xvfb
    sudo apt-get install python3-pip
    cd mame
    unzip mame.zip
    cd ..
    mv diambra/libdiambraEnv20.so diambra/libdiambraEnv.so
}

function setupMintTessa() {
    echo 'Updating APT'
    sudo apt update
    sudo apt-get update

    sudo apt-get install cmake libopenmpi-dev python3-dev zlib1g-dev
    sudo apt-get install libboost1.65-dev qt5-default libssl-dev libsdl2-ttf-dev xvfb
    sudo apt-get install python3-pip
    cd mame
    unzip mame.zip
    cd ..
    mv diambra/libdiambraEnv18.so diambra/libdiambraEnv.so

}

function setupUbuntuGroovyGorilla() {
    echo 'Updating APT'
    sudo apt update
    sudo apt-get update

    sudo apt-get install cmake libopenmpi-dev python3-dev zlib1g-dev
    sudo apt-get install libboost1.71-dev libboost-system1.71-dev libboost-filesystem1.71-dev qt5-default libssl-dev libsdl2-ttf-dev xvfb
    sudo apt-get install python3-pip
    cd mame
    unzip mame.zip
    cd ..
    mv diambra/libdiambraEnv20.so diambra/libdiambraEnv.so
}

function setupUbuntuBionicBeaver() {
    echo 'Updating APT'
    sudo apt update
    sudo apt-get update

    sudo apt-get install cmake libopenmpi-dev python3-dev zlib1g-dev
    sudo apt-get install libboost1.65-dev qt5-default libssl-dev libsdl2-ttf-dev xvfb
    sudo apt-get install python3-pip
    cd mame
    unzip mame.zip
    cd ..
    mv diambra/libdiambraEnv18.so diambra/libdiambraEnv.so

}

distroName=$(cat /etc/*-release | uniq -u | grep DISTRIB_ID)
distroRelease=$(cat /etc/*-release | uniq -u | grep DISTRIB_RELEASE)
IFS='='
read -ra array <<< "$distroName"
distroName=${array[1]}
read -ra array <<< "$distroRelease"
distroRelease=${array[1]}

if [ $distroName == "LinuxMint" ]; then
	if [ $distroRelease == "20.1" ]; then
		echo "Mint Ulyssa Detected"
        setupMintUlyssa
	elif [ $distroRelease == "19.1" ]; then
		echo "Mint Tessa Detected"
        setupMintTessa
	fi
fi

if [ $distroName == "Ubuntu" ]; then
	if [ $distroRelease == "20.10" ]; then
		echo "Ubuntu Groovy Gorilla Detected"
        setupUbuntuGroovyGorilla
	elif [ $distroRelease == "18.04" ]; then
		echo "Ubuntu Bionic Beaver Detected"
        setupUbuntuBionicBeaver
	fi
fi
