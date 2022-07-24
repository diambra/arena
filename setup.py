import setuptools, os
from pathlib import Path

try:
    from pip import main as pipmain
except ImportError:
    from pip._internal import main as pipmain

pipmain(['install', 'setuptools'])
pipmain(['install', 'distro'])

extras= {
    'core': []
}

# NOTE Package data is inside MANIFEST.In

setuptools.setup(
    name='diambra-arena',
    url='https://github.com/diambra/arena',
    version=os.environ.get('VERSION', '0.0.0'),
    author="DIAMBRA Team",
    author_email="info@diambra.ai",
    description="DIAMBRA™ Arena. Built with OpenAI Gym Python interface, easy to use,\ntransforms popular video games into Reinforcement Learning environments",
    long_description = (Path(__file__).parent / "README.md").read_text(),
    long_description_content_type="text/markdown",
    license='Custom',
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
        packages=[package for package in setuptools.find_packages(
        ) if package.startswith("diambra")],
    include_package_data=True,
    extras_require=extras,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Scientific/Engineering :: Artificial Life',
        'Topic :: Games/Entertainment',
        'Topic :: Games/Entertainment :: Arcade',
        'Topic :: Education',
    ]
)
