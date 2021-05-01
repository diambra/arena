from setuptools import setup
import platform
import distro
from setuptools.command.install import install
import setuptools

#TODO this for the PIP install manual
try:
    from pip import main as pipmain
except ImportError:
    from pip._internal import main as pipmain

#TODO add packages=["diambra"], depending on the installation and python_requires='>3.6'
class DiambraInstall(install):
    user_options = install.user_options

    def initialize_options(self):
        install.initialize_options(self)

    def finalize_options(self):
        import platform        
        plat=platform.system()
        if(plat != "Linux"):
            print("Warning, only Linux platforms are supported for this package")

        #subprocess.run("./setupOS.sh")
        pipmain(['install', 'distro'])
        import distro
        import subprocess

        distrib=distro.linux_distribution()
        name=distrib[0]
        release=float(distrib[1])

        if(not(name == "Ubuntu") and not(name == "Linux Mint")):
            print("Warning, only Ubuntu and Mint distros are supported for this package")
            sys.exit()

        print("Distro test ok, testing version of your current flavor")
        #NOTE This is the python-version of the script setupOS.sh #TODO to substitute with the option on setup (console_entry)
        aptCmd1="sudo apt-get update"
        aptCmd2_20="sudo apt-get install cmake libopenmpi-dev python3-dev zlib1g-dev libboost1.71-dev libboost-system1.71-dev ibboost-filesystem1.71-dev qt5-default libssl-dev libsdl2-ttf-dev xvfb python3-pip"
        aptCmd2_19="sudo apt-get install cmake libopenmpi-dev python3-dev zlib1g-dev libboost1.65-dev qt5-default libssl-dev ibsdl2-ttf-dev xvfb python3-pip"
        cpLib20="cp diambra_environment/diambraEnvLib/libdiambraEnv20.so diambra_environment/diambraEnvLib/libdiambraEnv.so"
        cpLib18="cp diambra_environment/diambraEnvLib/libdiambraEnv18.so diambra_environment/diambraEnvLib/libdiambraEnv.so"
        
        if(name == "Ubuntu"):
            if(release < 18.04):
                print("Warning, only LSB Bionic Beaver and Groovy Gorilla are supported for this package")
                sys.exit()
            if(release > 20):
                print("LSB Groovy Gorilla or higher")
                subprocess.run(aptCmd1.split())
                subprocess.run(aptCmd2_20.split())
                subprocess.run(cpLib20.split())
            else:
                print("LSB Bionic Beaver or higher")
                subprocess.run(aptCmd1.split())
                subprocess.run(aptCmd2_19.split())
                subprocess.run(cpLib18.split())
        
        if(name == "Linux Mint"):
            if(release < 19):
                print("Warning, only LSB Tessa and Ulyssa are supported for this package")
                sys.exit()
            if(release > 20):
                print("Mint Ulyssa")
                subprocess.run(aptCmd1.split())
                subprocess.run(aptCmd2_20.split())
                subprocess.run(cpLib20.split())
            else:
                print("Mint Tessa")
                subprocess.run(aptCmd1.split())
                subprocess.run(aptCmd2_19.split())
                subprocess.run(cpLib18.split())
        install.finalize_options(self)

    def run(self):
        install.run(self)

with open("README.md", "r") as description:
    long_description = description.read()

extras= {
	'core': [],
	'stable_baselines': ['python>=3.6']
	}

#NOTE This is the true creation of the setup env
#TODO From install add informations on package_data in order to get only stable_baselines info
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
            'opencv-contrib-python>=4.4.0.42',
            'opencv-python>=4.4.0.42'],
        packages=['diambra_environment','diambra_environment/customPolicies','diambra_environment/utils'],
        package_data={'diambra_environment' : ['diambra_environment/mame/mame.zip']},
        include_package_data=True,
        #data_files=['diambra_environment/diambraEnvLib/libdiambraEnv18.so','diambra_environment/diambraEnvLib/libdiambraEnv20.so','diambra_environment/mame/mame.zip'],
        extras_require=extras,
        classifiers=['Operating System :: Ubuntu 18.04 :: Ubuntu 20.04 :: Mint 19 Cinnamon :: Mint 20 Ulysse'],
        cmdclass={'install': DiambraInstall}
        )
