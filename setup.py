import distro
import platform
import setuptools

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

platform=platform.platform()
if(platform!="Linux"):
    print("Warning, only Linux platforms are supported for this package")

distro=distro.linux_distribution()
name=distro[0]
release=distro[1]

if(not(name.contains("Ubuntu")) and not(name.contains("Linux Mint"))):
    print("Warning, only Ubuntu and Mint distros are supported for this package")
    return

if(name.contains("Ubuntu")):
    if(not(release.contains("18.04")) and not(release.contains("20.10"))):
        print("Warning, only LSB Bionic Beaver and Groovy Gorilla are supported for this package")
        return

if(name.contains("Linux Mint")):
    if(not(release.contains("19")) and not(release.contains("20.1"))):
        print("Warning, only LSB Tessa and Ulyssa are supported for this package")
        return

with open("README.md", "r") as description:
    long_description = description.read()

setuptools.setup(
        name='diambra',
        version='0.2',
        scripts=['diambra'],
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
            'opencv-python>=4.4.0.42',
            'platform_system=="Linux""'],
        classifiers=['Operating System :: Ubuntu 18.04 :: Ubuntu 20.04 :: Mint 19 Cinnamon :: Mint 20 Ulysse'],
        cmdclass={'install': DiambraInstall}
        )
