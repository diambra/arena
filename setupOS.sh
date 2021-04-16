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
    mv diambraEnvLib/libdiambraEnv20.so diambraEnvLib/libdiambraEnv.so
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
    mv diambraEnvLib/libdiambraEnv18.so diambraEnvLib/libdiambraEnv.so

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
    mv diambraEnvLib/libdiambraEnv20.so diambraEnvLib/libdiambraEnv.so
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
    mv diambraEnvLib/libdiambraEnv18.so diambraEnvLib/libdiambraEnv.so

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
	isTessa=$(echo $distroRelease" > 19" | bc)
	if [ $isUlyssa -eq 1 ]; then
		echo "Mint Ulyssa Detected"
        	#setupMintUlyssa
	elif [ $isTessa -eq 1 ]; then
		echo "Mint Tessa Detected"
        	#setupMintTessa
	else
		echo "Mint version not supported"
	fi
fi

if [ $distroName == "Ubuntu" ]; then
	isAtLeastGorilla=$(echo $distroRelease" > 20" | bc)
	isAtLeastBionicBeaver=$(echo $distroRelease" > 18" | bc)
	if [ $isAtLeastGorilla -eq 1 ]; then
		echo "Ubuntu Groovy Gorilla Detected"
        #setupUbuntuGroovyGorilla
	elif [ $isAtLeastBionicBeaver -eq 1 ]; then
		echo "Ubuntu Bionic Beaver Detected"
        #setupUbuntuBionicBeaver
    else
		echo "Ubuntu version not supported"
	fi
fi
