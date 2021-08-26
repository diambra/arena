import platform

try:
    from pip import main as pipmain
except ImportError:
    from pip._internal import main as pipmain

import platform
plat=platform.system()
if(plat != "Linux"):
    print("Warning, only Linux platforms are supported for this package")

pipmain(['install', 'setuptools'])
import setuptools
from setuptools.command.install import install
from setuptools import setup
import os
pipmain(['install', 'distro'])
import distro

distrib=distro.linux_distribution()
name=distrib[0]
release=float(distrib[1])

if(not(name == "Ubuntu") and not(name == "Linux Mint")):
    print("Warning, only Ubuntu and Mint distros are supported for this package")
    sys.exit()

print("Distro test ok, testing version of your current flavor")
aptCmd1="sudo apt-get update --assume-yes"
#MAIN Packages Required
aptCmd2_20="sudo apt-get --assume-yes install libboost1.71-dev libboost-system1.71-dev ibboost-filesystem1.71-dev qt5-default libssl-dev libsdl2-ttf-dev xvfb python3-pip"
aptCmd2_19="sudo apt-get install --assume-yes libboost1.65-dev qt5-default libssl-dev ibsdl2-ttf-dev xvfb python3-pip"
#Stable-baselines specific packages
aptCmdSb_20="sudo apt-get install --assume-yes cmake libopenmpi-dev python3-dev zlib1g-dev"
aptCmdSb_19="sudo apt-get install --assume-yes cmake libopenmpi-dev python3-dev zlib1g-dev"
#Diambra Lib commands
cpLib20="cp diambra_environment/diambraEnvLib/libdiambraEnv20.so diambra_environment/diambraEnvLib/libdiambraEnv.so"
cpLib18="cp diambra_environment/diambraEnvLib/libdiambraEnv18.so diambra_environment/diambraEnvLib/libdiambraEnv.so"
#MAME Cmd
unzipMameCmd="unzip diambra_environment/mame/mame.zip -d diambra_environment/mame"

if(name == "Ubuntu"):
    if(release < 18.04):
        print("Warning, only LSB Bionic Beaver and Groovy Gorilla are supported for this package")
        sys.exit()
    if(release > 20):
        print("LSB Groovy Gorilla or higher")
#        os.system(aptCmd1)
#        os.system(aptCmd2_20)
#        if(True):
#            os.system(aptCmdSb_20)
        os.system(cpLib20)
    else:
        print("LSB Bionic Beaver or higher")
#        os.system(aptCmd1)
#        os.system(aptCmd2_19)
#        if(True):
#            os.system(aptCmdSb_19)
        os.system(cpLib18)

if(name == "Linux Mint"):
    if(release < 19):
        print("Warning, only LSB Tessa and Ulyssa are supported for this package")
        sys.exit()
    if(release > 20):
        print("Mint Ulyssa")
#        os.system(aptCmd1)
#        os.system(aptCmd2_20)
#        if(True):
#            os.system(aptCmdSb_20)
        os.system(cpLib20)
    else:
        print("Mint Tessa")
#        os.system(aptCmd1)
#        os.system(aptCmd2_19)
#        if(True):
#            os.system(aptCmdSb_19)
        os.system(cpLib18)

os.system(unzipMameCmd)

#NOTE Not useful for now
#class DiambraInstall(install):
#    user_options = install.user_options

#    def initialize_options(self):
#        install.initialize_options(self)

#    def finalize_options(self):
#        install.finalize_options(self)

#    def run(self):
#        install.run(self)

with open("README.md", "r") as description:
    long_description = description.read()

extras= {
	'core': []
	}

#NOTE Package data is inside MANIFEST.In

setuptools.setup(
        name='DIAMBRAEnvironment',
        url='https://github.com/diambra/DIAMBRAenvironment',
        version='0.2',
        author="Artificial Twin",
        author_email="diambra@artificialtwin.com",
        description="DIAMBRA™ | Dueling AI Arena. Built with OpenAI Gym standard, easy to use,\ntransforms famous classic videogames into Reinforcement Learning tasks",
        long_description=long_description,
        long_description_content_type="Reinforcement Learning",
        license='GNU Affero GPL',
        install_requires=[
            'pip>=21',
            'setuptools',
            'distro>=1',
            'gym>=0.17.1',
            'jupyter>=1.0.0',
            'testresources',
            'inputs',
            'opencv-contrib-python>=4.4.0.42',
            'opencv-python>=4.4.0.42'],
        packages=['diambra_environment','diambra_environment/customPolicies','diambra_environment/utils'],
        include_package_data=True,
        extras_require=extras,
        classifiers=['Operating System :: Ubuntu 18.04 :: Ubuntu 20.04 :: Mint 19 Cinnamon :: Mint 20 Ulysse']
        )

#DIAMBRA Lib Clear Cmd
clearLibCmd="rm diambra_environment/diambraEnvLib/libdiambraEnv.so"
os.system(clearLibCmd)
#MAME Clear Cmd
clearMameCmd="rm diambra_environment/mame/mame"
os.system(clearMameCmd)
