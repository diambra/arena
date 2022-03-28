import platform, sys

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
from setuptools import setup, find_packages
import os
pipmain(['install', 'distro'])
import distro

distrib=distro.linux_distribution()
name=distrib[0]
release=float(distrib[1])

if(not(name == "Ubuntu") and not(name == "Linux Mint")):
    print("Warning, only Ubuntu and Mint distros are supported for this package")
    sys.exit(1)

print("Distro test ok, testing version of your current flavor")
#Diambra Lib commands
cpLib20="cp diambraArena/diambraEnvLib/libdiambraEnv20.so diambraArena/diambraEnvLib/libdiambraEnv.so"
cpLib18="cp diambraArena/diambraEnvLib/libdiambraEnv18.so diambraArena/diambraEnvLib/libdiambraEnv.so"
#MAME Cmd
unzipMameCmd="unzip diambraArena/mame/mame.zip -d diambraArena/mame"

if(name == "Ubuntu"):
    if(release < 18.04):
        print("Warning, only LSB Bionic Beaver and Groovy Gorilla are supported for this package")
        sys.exit(1)
    if(release > 20):
        print("LSB Groovy Gorilla or higher")
        os.system(cpLib20)
    else:
        print("LSB Bionic Beaver or higher")
        os.system(cpLib18)

if(name == "Linux Mint"):
    if(release < 19):
        print("Warning, only LSB Tessa and Ulyssa are supported for this package")
        sys.exit(1)
    if(release > 20):
        print("Mint Ulyssa")
        os.system(cpLib20)
    else:
        print("Mint Tessa")
        os.system(cpLib18)

os.system(unzipMameCmd)

extras= {
	'core': []
	}

#NOTE Package data is inside MANIFEST.In

setuptools.setup(
        name='diambraArena',
        url='https://github.com/diambra/DIAMBRAenvironment',
        version='1.0',
        author="DIAMBRA Team",
        author_email="info@diambra.ai",
        description="DIAMBRA™ Arena. Built with OpenAI Gym Python interface, easy to use,\ntransforms popular video games into Reinforcement Learning environments",
        long_description="DIAMBRA™ Arena. Built with OpenAI Gym Python interface, easy to use,\ntransforms popular video games into Reinforcement Learning environments",
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
            'screeninfo',
            'tk',
            'opencv-contrib-python>=4.4.0.42',
            'opencv-python>=4.4.0.42'],
        #packages=['diambraArena','diambraArena/wrappers','diambraArena/utils'],
        packages=[package for package in find_packages() if package.startswith("diambraArena")],
        include_package_data=True,
        extras_require=extras,
        classifiers=['Operating System :: Ubuntu 18.04 :: Ubuntu 20.04 :: Mint 19 Cinnamon :: Mint 20 Ulysse']
        )

#DIAMBRA Lib Clear Cmd
clearLibCmd="rm diambraArena/diambraEnvLib/libdiambraEnv.so"
os.system(clearLibCmd)
#MAME Clear Cmd
clearMameCmd="rm diambraArena/mame/mame"
os.system(clearMameCmd)
