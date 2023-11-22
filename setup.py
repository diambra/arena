import os
from pathlib import Path

import setuptools

try:
    from pip import main as pipmain
except ImportError:
    from pip._internal import main as pipmain

pipmain(["install", "setuptools"])
pipmain(["install", "distro"])

extras = {
    "core": [],
    "tests": ["pytest", "pytest-mock", "testresources"],
    "stable-baselines": [
        "stable-baselines~=2.10.2",
        "gym<=0.21.0",
        "protobuf==3.20.1",
        "pyyaml",
    ],
    "stable-baselines3": ["stable-baselines3[extra]~=2.1.0", "pyyaml"],
    "ray-rllib": ["ray[rllib]~=2.7.0", "tensorflow", "torch", "pyyaml"],
    "sheeprl": [
        "sheeprl==0.4.6",
        "importlib-resources==6.1.0",
    ],
}

# NOTE Package data is inside MANIFEST.In

setuptools.setup(
    name="diambra-arena",
    url="https://github.com/diambra/arena",
    version=os.environ.get("VERSION", "0.0.0"),
    author="DIAMBRA Team",
    author_email="info@diambra.ai",
    description="DIAMBRA™ Arena. Built with OpenAI Gym Python interface, easy to use, transforms popular video games into Reinforcement Learning environments",
    long_description=(Path(__file__).parent / "README.md").read_text(),
    long_description_content_type="text/markdown",
    license="Custom",
    install_requires=[
        "pip>=21",
        'importlib-metadata<=4.12.0; python_version <= "3.7"',  # problem with gym for importlib-metadata==5.0.0 and python <=3.7
        "setuptools",
        "distro>=1",
        "gymnasium>=0.26.3",
        "inputs",
        "screeninfo",
        "tk",
        "opencv-python>=4.4.0.42",
        "grpcio",
        "diambra-engine~=2.2.0",
        "dacite",
    ],
    packages=[
        package
        for package in setuptools.find_packages()
        if package.startswith("diambra")
    ],
    include_package_data=True,
    extras_require=extras,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Artificial Life",
        "Topic :: Games/Entertainment",
        "Topic :: Games/Entertainment :: Arcade",
        "Topic :: Education",
    ],
)
