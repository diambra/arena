# DIAMBRA Environment

## Summary

- [What is DIAMBRA](#what-is-diambra)
- [Interfaced Games](#interfaced-games)
- [Requirements](#requirements)
- [Getting Started](#getting-started)
- [Citation](#citation)

## What is DIAMBRA

![diambra](https://raw.githubusercontent.com/diambra/DIAMBRAenvironment/main/img/github.png)

DIAMBRA Environment is a software package that allows you to use famous videogames as Reinforcement Learning tasks. It provides a python interface that follows the standard de-facto in this field, [OpenAI Gym](https://gym.openai.com/), so it is super easy to use, as demonstrated by the following code snippet:

```
from diambraGym import diambraGym

base_path = "/home/path-to-repo-root/" # Edit accordingly

diambraEnvKwargs = {}
diambraEnvKwargs["gameId"]          = "doapp" # Game selection
diambraEnvKwargs["diambraEnv_path"] = base_path + "diambraEnvLib/"
diambraEnvKwargs["roms_path"]       = base_path + "roms/" # Absolute path to roms
diambraEnvKwargs["mame_path"]       = base_path + "mame/" # Absolute path to MAME executable

diambraEnvKwargs["mame_diambra_step_ratio"] = 6
diambraEnvKwargs["render"]                  = True # Renders the environment, deactivate for speedup
diambraEnvKwargs["lock_fps"]                = True # Locks to 60 FPS
diambraEnvKwargs["sound"]                   = diambraEnvKwargs["lock_fps"] and diambraEnvKwargs["render"]

# 1P
diambraEnvKwargs["player"] = "P1"

# Game specific
diambraEnvKwargs["difficulty"]  = 3
diambraEnvKwargs["characters"]  = [["Random", "Random"], ["Random", "Random"]]
diambraEnvKwargs["charOutfits"] = [2, 2]

env = diambraGym("Test", diambraEnvKwargs)

observation = env.reset()

for _ in range(100):
            
    actions = env.action_spaces[0].sample() # Sampling for 1P mode
              
    observation, reward, done, info = env.step(actions)
    
    if done:
        observation = env.reset()
        
env.close()
```

Included in the repo you find python notebooks showing you in detail how to:
- Use DIAMBRA Gym Class (`DiambraGymTest.ipynb`)
- Use DIAMBRA Gym Wrappers (`DiambraGymWrapTest.ipynb`)
- Train a state of the art Reinforcement Learning algorithm (`DiambraAIAgent.ipynb`)

In addition, on <a href="https://diambra.artificialtwin.com" target="_blank">DIAMBRA website</a> you find a collection of <a href="https://diambra.artificialtwin.com/downloadenv/#tutorials" target="_blank">video tutorials</a> providing a step by step guide for a flawless adoption. 

![diambraGif](https://raw.githubusercontent.com/diambra/DIAMBRAenvironment/main/img/github.gif)

For additional insights and cool stuff about this initiative, follow the live stream on our [Twitch channel](https://www.twitch.tv/diambra_at), every Tuesday and Thursday at 10 PM CET = 1 PM PT!

## Interfaced games

This is the list of currently interfaced games:
- Dead Or Alive ++
- Street Fighter III: 3rd Strike (Coming Soon)
- Tekken Tag Tournament (Coming Soon)
- Ultimate Mortal Kombat III (Coming Soon)

## Requirements

### Hardware

- (*) 16 Gb Ram
- (*) 4 Gb GPU

### Operating System

- Linux Mint 19 or newer
- Linux Ubuntu 18.04 or newer

### OS Packages

##### Mint 19 / Ubuntu 18

`sudo apt-get install libboost1.65-dev libssl-dev libsdl2-ttf-dev`

##### Mint 20 / Ubuntu 20

`sudo apt-get install libboost1.71-dev libboost-system1.71-dev libssl-dev libsdl2-ttf-dev`

##### (*) Mint / Ubuntu

`sudo apt-get install cmake libopenmpi-dev python3-dev zlib1g-dev`

### Python Packages

A working python environment configuration can be found inside the repository: the file `diambraCondaExport.yml` provides a working conda environment packages list allowing to run every script contained here. Main packages to install are:

- `pip install jupyter opencv-python gym`
-  (*)(**) `pip install stable-baselines[mpi]`

### Repository content

SHA256 for each rom are found in the `json` file inside the `roms/` folder

### Generic recommendations

Use a Python Virtual Environment to manage dependencies ([VirtualEnv](https://virtualenv.pypa.io/en/latest/) or [[Ana]Conda](https://docs.conda.io/projects/conda/en/latest/index.html))


(*)  Specific for PPO Algorithm (based on Stable Baselines Reinforcement Learning library)

(**) For additional details on Stable Baselines dependencies, visit their documentation [here](https://stable-baselines.readthedocs.io/en/master/guide/install.html).

## Getting started

### General advice

- Make sure you are connected to the Internet when running the environment
- Extract `mame` binary contained in `mame/mame.zip` archive and place it inside `mame/` folder
- Rename DIAMBRA Environment library file inside `diambraEnvLib/` folder:
    - Mint 19 / Ubuntu 18: rename `libdiambraEnv18.so` to `libdiambraEnv.so`
    - Mint 20 / Ubuntu 20: rename `libdiambraEnv20.so` to `libdiambraEnv.so`
- Download games roms and place them in a folder of choice
    - **WARNING #1**: Downloading roms can be illegal depending on different conditions and country. It is your sole and only responsibility to make sure you respect the law. More info can be found [here](https://wiki.mamedev.org/index.php/FAQ:ROMs).
    - **WARNING #2**: Only a specific rom will work for each game. It is uniquely identified by means of it SHA256 sum value. Check it with the specific shell command:

       `sha256sum path-to-file`

- Absolute `base_path` inside Jupyter Notebooks has to be updated accordingly to where you extracted/clone the repository
- Paths to `mame/` and `diambraEnvLib/` folders are needed, if you move them from the downloaded archive, make sure to update them accordingly
- Watch our <a href="https://diambra.artificialtwin.com/downloadenv/#tutorials" target="_blank">tutorials</a> for a step by step walkthrough
- Join our <a href="https://discord.gg/YSBjtmvefc" target="_blank">Discord server</a> to interact with other developers and share ideas and questions, or simply have a chat!

## Citation
```
  @misc{diambra2021
    author = {Alessandro Palmas},
    title = {DIAMBRA Environment, Gym Compliant Interface For Famous Videogames},
    year = {2021},
    howpublished = {\url{https://github.com/diambra/DIAMBRAenvironment}},
  }
```

###### DIAMBRA™ is a Trade Mark, property of and made with :heart: by <a href="https://artificialtwin.com" target="_blank">Artificial Twin</a>, © Copyright 2018 - 2021.
