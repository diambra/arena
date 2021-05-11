# DIAMBRA Environment

**🧪 PLEASE NOTE THAT THIS SOFTWARE IS STILL IN ALPHA ⚗️**

**⚠️ BREAKING CHANGES MAY OCCUR ⚠️**

## Summary

- **[What is DIAMBRA Environment](#what-is-diambra-environment)**
- **[Interfaced Games](#interfaced-games)**
- **[Installation](#installation)**
- **[Getting Started and Examples](#getting-started-and-examples)**
- **[AI Tournament](#ai-tournament)**
- **[Troubleshoot](#support-and-troubleshoot)**
- **[Citation](#citation)**

## What is DIAMBRA Environment

![diambra](https://raw.githubusercontent.com/diambra/DIAMBRAenvironment/main/img/github.png)

**DIAMBRA Environment** is a software package that **transforms famous videogames in Reinforcement Learning tasks**. It provides a **python interface** that follows the standard de-facto in this field, **[OpenAI Gym](https://gym.openai.com/)**, so it is **super easy to use**, and **supports headless mode** for server-side executions too.

### Interfaced games

List of currently interfaced games:
- Dead Or Alive ++
- Street Fighter III: 3rd Strike (Coming Soon)
- Tekken Tag Tournament (Coming Soon)
- Ultimate Mortal Kombat III (Coming Soon)
- Many more in development ...

**Note**: roms are identified via SHA256 signatures, the correct value for each game is found in the `json` file inside the `roms/` folder

## Installation

### Prerequisites

##### Operating System

- Linux Mint 19 or newer
- Linux Ubuntu 18.04 or newer

##### (Optional) Python Virtual Environment

We recommend to use a Virtual Environment to manage dependencies, both [VirtualEnv](https://virtualenv.pypa.io/en/latest/) and [[Ana]Conda](https://docs.conda.io/projects/conda/en/latest/index.html) have been tested.

### Core

Execute following commands from inside the repo root

 - Install OS dependencies: `./setupOS.sh`
 - Install Python packages: `pip3 install .`

### Stable-Baselines Additional Support

Execute following commands from inside the repo root

 - Install OS dependencies: `./setupOS.sh -s`
 - Install Python packages: 
   - `pip3 install .[stable-baselines]`
   - (*)`pip3 install tensorflow-gpu==1.14.0` **OR** `pip3 install tensorflow==1.14.0` for GPU/CPU versions


(*) Python 3.6.x is required. OS like Ubuntu 20.10 requires to install it from [sources](https://www.python.org/downloads/).

## Getting started and Examples

- Make sure you are connected to the Internet when running the environment
- Download games roms and place them in a folder of choice (default to `repo-root/roms/`)
    - **WARNING #1**: Downloading roms can be illegal depending on different conditions and country. It is your sole and only responsibility to make sure you respect the law. More info can be found [here](https://diambra.artificialtwin.com/terms/) and [here](https://wiki.mamedev.org/index.php/FAQ:ROMs).
    - **WARNING #2**: Only a specific rom will work for each game. It is uniquely identified by means of it SHA256 sum value. Check it with the specific shell command:

       `sha256sum path-to-rom-file`

### Examples

Basic usage:

```
# Code from /examples/core/diambraGymGist.py
from diambra_environment.diambraGym import diambraGym
import os

repo_base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../") # Absolute path to your DIAMBRA environment repo

diambraEnvKwargs = {}
diambraEnvKwargs["gameId"]          = "doapp" # Game selection
diambraEnvKwargs["roms_path"]       = os.path.join(repo_base_path, "roms/") # Absolute path to roms

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

envId = "TestEnv" # This ID must be unique for every instance of the environment when using diambraGym class
env = diambraGym(envId, diambraEnvKwargs, headless=False) # Use `headless=True` for server-side executions

observation = env.reset()

for _ in range(100):

    actions = env.action_spaces[0].sample() # Sampling for 1P mode

    observation, reward, done, info = env.step(actions)

    if done:
        observation = env.reset()

env.close()
```

In the `examples/` folder you find **python notebooks**, showing in detail how to:

##### Core

- Use DIAMBRA Gym Class (`examples/core/DiambraGymTest.ipynb`)
- Use DIAMBRA Gym Wrappers (`examples/core/DiambraGymWrapTest.ipynb`)
- Use DIAMBRA Gym Wrappers to record expert demonstrations for Imitation Learning (`examples/core/DiambraGymRecTest.ipynb`)
- Use DIAMBRA Imitation Learning Gym to use recorded expert demonstrations (Single Env) (`examples/core/DiambraImitationLearningTest.ipynb`)

##### Stable-Baselines (Require Installation with Stable-Baselines Additional Support)

- Use DIAMBRA Imitation Learning Gym to use recorded expert demonstrations (Vectorized Envs Via Stable-Baselines) (`examples/stable_baselines/DiambraImitationLearningVecEnvTest.ipynb`)
- Train a state of the art Reinforcement Learning algorithm (`examples/stable_baselines/DiambraAIAgent.ipynb`)

In addition, on <a href="https://diambra.artificialtwin.com" target="_blank">DIAMBRA's website</a> you **find a collection of <a href="https://diambra.artificialtwin.com/downloadenv/#tutorials" target="_blank">video tutorials</a>** providing a step by step guide for a flawless adoption. 

![diambraGif](https://raw.githubusercontent.com/diambra/DIAMBRAenvironment/main/img/github.gif)

For additional insights and cool stuff about this initiative, **join our <a href="https://discord.gg/tFDS2UN5sv" target="_blank">Discord server</a> to interact with other developers and share ideas and questions** and **follow the live stream on our [Twitch channel](https://www.twitch.tv/diambra_at)**, every Tuesday and Thursday at 10 PM CET = 1 PM PT!

## AI Tournament

![diambraAITournament](https://raw.githubusercontent.com/diambra/DIAMBRAenvironment/main/img/WideFlyer.jpg)

We just launched an **international competition** where each participant will **train an AI agent to effectively play Dead Or Alive ++** using the environment contained in this repository.

All validly submitted agents will be evaluated with **gameplays streamed live on our [Twitch channel](https://www.twitch.tv/diambra_at)**, with commentary and a lot of cool stuff. It is gonna be exciting!

**[Register here](https://diambra.artificialtwin.com/aitournament/)**

## Support and Troubleshoot

The fastest way to receive support is by joining DIAMBRA <a href="https://discord.gg/tFDS2UN5sv" target="_blank">Discord server</a> and use the dedicated channel.

### Common Known Problems

 - If you are receiving the **Runtime error "An attempt has been made to start a new process before the current process has finished its bootstrapping phase."** when running python scripts extracted from notebooks, you can fix it placing `if __name__ == '__main__':` after modules import in the script.
 - If the **environment freezes or if your receive the Runtime error "Connection refused by peer"**, make sure you reserve the whole machine to execute the environment, avoid running additional tasks, even light ones like browsing the internet
 - If the **environment is not working and you receive LUA errors in the terminal** (typically in between environment initialization and environment reset), make sure you placed the environment folder in the OS drive with an `ext4` filesystem (mounted `NTFS` data drives can cause problems)

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
