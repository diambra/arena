import platform
#import setuptools
import subprocess
import sys
import getopt

#TODO this for the PIP install manual
try:
    from pip import main as pipmain
except ImportError:
    from pip._internal import main as pipmain

#TODO add packages=["diambra"], depending on the installation and python_requires='>3.6'
#from setuptools.command.install import install
#class DiambraInstall(install):
#    user_options = install.user_options + [
#        ('stablebaseline', None, 'Core or stablebaseline installation')
#    ]
#
#    def initialize_options(self):
#        install.initialize_options(self)
#        self.stablebaseline = 0
#
#    def finalize_options(self):
#        install.finalize_options(self)
#
#    def run(self):
#        stablebaseline = self.stablebaseline
#        install.run(self)

arg=sys.argv[1:]
if(arg == "stablebaseline"):
    if(sys.version_info < (3, 6)):
        print("Warning, update your Python version to 3.6 at least to use stablebaseline")
        sys.exit()


platform=platform.system()
if(platform != "Linux"):
    print("Warning, only Linux platforms are supported for this package")

subprocess.run("./setupOS.sh")
pipmain(['install', 'distro'])
import distro

distro=distro.linux_distribution()
name=distro[0]
release=float(distro[1])

if(not(name == "Ubuntu") and not(name == "Linux Mint")):
    print("Warning, only Ubuntu and Mint distros are supported for this package")
    sys.exit()


#NOTE This is the python-version of the script setupOS.sh #TODO to substitute with the option on setup (console_entry)
#aptCmd1="sudo apt-get update"
#aptCmd2_20="sudo apt-get install cmake libopenmpi-dev python3-dev zlib1g-dev libboost1.71-dev libboost-system1.71-dev ibboost-filesystem1.71-dev qt5-default libssl-dev libsdl2-ttf-dev xvfb python3-pip"
#aptCmd2_19="sudo apt-get install cmake libopenmpi-dev python3-dev zlib1g-dev libboost1.65-dev qt5-default libssl-dev ibsdl2-ttf-dev xvfb python3-pip"
#
#if(name == "Ubuntu"):
#    if(release < 18.04):
#        print("Warning, only LSB Bionic Beaver and Groovy Gorilla are supported for this package")
#        sys.exit()
#    if(release > 20):
#        subprocess.run(aptCmd1.split())
#        subprocess.run(aptCmd2_20.split())
#    else:
#        subprocess.run(aptCmd1.split())
#        subprocess.run(aptCmd2_19.split())
#
#if(name == "Linux Mint"):
#    if(release < 19):
#        print("Warning, only LSB Tessa and Ulyssa are supported for this package")
#        sys.exit()
#    if(release > 20):
#        subprocess.run(aptCmd1.split())
#        subprocess.run(aptCmd2_20.split())
#    else:
#        subprocess.run(aptCmd1.split())
#        subprocess.run(aptCmd2_19.split())

#NOTE this part is the manual PIP Installation
pipmain(['install', 'setuptools'])
pipmain(['install', 'pip>=21'])
pipmain(['install', 'gym>=0.17.1'])
pipmain(['install', 'jupyter>=1.0.0'])
pipmain(['install', 'opencv-contrib-python>=4.4.0.42'])
pipmain(['install', 'opencv-python>=4.4.0.42'])

#with open("README.md", "r") as description:
#    long_description = description.read()

#NOTE This is the true creation of the setup env
#setuptools.setup(
#        name='DIAMBRAEnvironment',
#        url='https://github.com/diambra/DIAMBRAenvironment',
#        version='0.2',
#        author="Artificial Twin",
#        author_email="alessandropalmas.mail@gmail.com",
#        description="The virtual arena where AI Algorithms fight in video games matches with live technical commentary",
#        long_description=long_description,
#        long_description_content_type="Reinforcement Learning",
#        license='GNU Affero GPL',
#        install_requires=[
#            'pip>=21',
#            'gym>=0.17.1',
#            'jupyter>=1.0.0',
#            'opencv-contrib-python>=4.4.0.42',
#            'opencv-python>=4.4.0.42'],	
#        classifiers=['Operating System :: Ubuntu 18.04 :: Ubuntu 20.04 :: Mint 19 Cinnamon :: Mint 20 Ulysse'],
#        cmdclass={'install': DiambraInstall}
#        )
