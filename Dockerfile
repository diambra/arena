#Create Base Image
FROM ubuntu
#Install basic packages
RUN apt-get update -y
#Stable Baselines Packages
RUN apt-get install cmake libopenmpi-dev python3-dev zlib1g-dev -y
#Packages that must be always installed
RUN apt-get install libboost1.71-dev libboost-system1.71-dev libboost-filesystem1.71-dev qt5-default libssl-dev libsdl2-ttf-dev xvfb python3-pip jupyter -y
RUN pip3 install --upgrade pip
#Expose a port? Example: EXPOSE 80
#Entry Point of a program? ENTRYPOINT [ "/usr/sbin/shutdown" ]
