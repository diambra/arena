import distro
import platform
import setuptools
import subprocess
import sys

from setuptools.command.install import install

class DiambraInstall(install):
    user_options = install.user_options + [
        ('option', None, 'Core or stablebaseline installation')
    ]

    def initialize_options(self):
        install.initialize_options(self)
        self.option = None

    def finalize_options(self):
        install.finalize_options(self)

    def run(self):
        global option
        option = self.option
        install.run(self)

platform=platform.system()
if(platform != "Linux"):
    print("Warning, only Linux platforms are supported for this package")

distro=distro.linux_distribution()
name=distro[0]
release=float(distro[1])

if(not(name == "Ubuntu") and not(name == "Linux Mint")):
    print("Warning, only Ubuntu and Mint distros are supported for this package")
    sys.exit()

aptCmd1="sudo apt-get update"
aptCmd2_20="sudo apt-get install cmake libopenmpi-dev python3-dev zlib1g-dev libboost1.71-dev libboost-system1.71-dev libboost-filesystem1.71-dev qt5-default libssl-dev libsdl2-ttf-dev xvfb python3-pip"
aptCmd2_19="sudo apt-get install cmake libopenmpi-dev python3-dev zlib1g-dev libboost1.65-dev qt5-default libssl-dev libsdl2-ttf-dev xvfb python3-pip"

if(name == "Ubuntu"):
    if(release < 18.04):
        print("Warning, only LSB Bionic Beaver and Groovy Gorilla are supported for this package")
        sys.exit()
    if(release > 20):
        subprocess.run(aptCmd1.split())
        subprocess.run(aptCmd2_20.split())
    else:
        subprocess.run(aptCmd1.split())
        subprocess.run(aptCmd2_19.split())

if(name == "Linux Mint"):
    if(release < 19):
        print("Warning, only LSB Tessa and Ulyssa are supported for this package")
        sys.exit()
    if(release > 20):
        subprocess.run(aptCmd1.split())
        subprocess.run(aptCmd2_20.split())
    else:
        subprocess.run(aptCmd1.split())
        subprocess.run(aptCmd2_19.split())

with open("README.md", "r") as description:
    long_description = description.read()

setuptools.setup(
        name='DIAMBRAEnvironment',
        url='https://github.com/diambra/DIAMBRAenvironment',
        version='0.2',
        author="Artificial Twin",
        author_email="alessandropalmas.mail@gmail.com",
        description="The virtual arena where AI Algorithms fight in video games matches with live technical commentary",
        long_description=long_description,
        long_description_content_type="Reinforcement Learning",
        license='GNU Affero GPL',
        install_requires=[
            'gym>=0.17.1',
            'jupyter>=1.0.0',
            'opencv-contrib-python>=4.4.0.42',
            'opencv-python>=4.4.0.42'],	
	packages=["diambra"],
        classifiers=['Operating System :: Ubuntu 18.04 :: Ubuntu 20.04 :: Mint 19 Cinnamon :: Mint 20 Ulysse'],
        cmdclass={'install': DiambraInstall}
        )
