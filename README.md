![diambra](https://raw.githubusercontent.com/diambra/DIAMBRAenvironment/main/img/github.png)

# DIAMBRA Arena

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

**!! WIN and MacOS support (via Docker) under development and available soon, STAY TUNED!**

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

```python
import diambraArena

# Mandatory settings
settings = {}
# Game selection
settings["gameId"] = "doapp"
# Path to roms folder
settings["romsPath"] = opt.romsPath

env = diambraArena.make("TestEnv", settings)

observation = env.reset()

while True:

    actions = env.action_space.sample()

    observation, reward, done, info = env.step(actions)

    if done:
        observation = env.reset()
        break

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

For additional insights and cool stuff about this initiative, **join our <a href="https://discord.gg/tFDS2UN5sv" target="_blank">Discord server</a> to interact with other developers and share ideas and questions**, and **follow the live stream on our [Twitch channel](https://www.twitch.tv/diambra_at)**, every Tuesday and Thursday at 10 PM CET = 1 PM PT!

## AI Tournament

![diambraAITournament](https://raw.githubusercontent.com/diambra/DIAMBRAenvironment/main/img/WideFlyer.jpg)

Our very first AI Tournament just ended, and **it was amazing!** Participants trained an AI algorithm to effectively play Dead Or Alive++. The three best algorithms participated in the final event and **competed for the 1400 CHF prize.**

**Stay tuned for tons more!**

**[Read more and watch related events here](https://diambra.artificialtwin.com/aitournament/)**

## Support and Troubleshoot

The fastest way to receive support is by joining DIAMBRA <a href="https://discord.gg/tFDS2UN5sv" target="_blank">Discord server</a> and use the dedicated channel.

## Citation
```
  @misc{diambra2022
    author = {Alessandro Palmas},
    title = {DIAMBRA Arena: built with OpenAI Gym Python interface, easy to use, transforms popular video games into Reinforcement Learning environments.},
    year = {2022},
    howpublished = {\url{https://github.com/diambra/diambraArena}},
  }
```

## Terms of Use

###### DIAMBRA™ is a Trade Mark, © Copyright 2018 - 2022. All Right Reserved.
