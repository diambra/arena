# Create Base Image (Ubuntu 18.04)
FROM ubuntu:bionic

# Fix hang in TZ
ENV TZ=America/Los_Angeles
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install basic packages (Update OS)
RUN apt-get update -y

# Packages that must be always installed
RUN apt-get install libboost1.65-dev qt5-default libssl-dev libsdl2-ttf-dev xvfb python3-pip jupyter unzip python3-tk -y
RUN pip3 install --upgrade pip

# Copy diambraArena Repo
RUN mkdir /diambraArena
COPY . /diambraArena
WORKDIR /diambraArena/
RUN pip3 install .

#Expose a port? Example: EXPOSE 80
#Entry Point of a program? ENTRYPOINT [ "/usr/sbin/shutdown" ]
