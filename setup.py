from setuptools import find_packages
import setuptools
import sys
import os

# Check if docker is installed
if os.system("docker ps") != 0:
    print("---")
    print("ERROR: It seems docker is not installed in your system.")
    print("It is required to use DIAMBRA Arena.")
    print("Install it from https://docs.docker.com/get-docker/")
    print("---")
    sys.exit(1)
else:
    print("Downloading DIAMBRA Docker image")
    # TODO: decomment
    # os.system("docker pull diambra/diambraApp:main")

try:
    from pip import main as pipmain
except ImportError:
    from pip._internal import main as pipmain

pipmain(['install', 'setuptools'])
pipmain(['install', 'distro'])

extras = {
    'core': []
}

# NOTE Package data is inside MANIFEST.In

setuptools.setup(
    name='diambraArena',
    url='https://github.com/diambra/diambraArena',
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
            'opencv-python>=4.4.0.42',
            'grpcio',
            'grpcio-tools'],
    # packages=['diambraArena','diambraArena/wrappers','diambraArena/utils'],
        packages=[package for package in find_packages(
        ) if package.startswith("diambraArena")],
    include_package_data=True,
    extras_require=extras
)
