![diambra](https://raw.githubusercontent.com/diambra/DIAMBRAenvironment/main/img/github.png)

# DIAMBRA Arena

DIAMBRA Arena is a software package featuring a collection of **high-quality environments for Reinforcement Learning research and experimentation**. It acts as an interface towards popular arcade emulated video games, offering a **Python API fully compliant with OpenAI Gym standard**, that makes its adoption smooth and straightforward.

It **supports all major Operating Systems: Linux, Windows and MacOS**, most of them via Docker, with a step by step installation guide available in this manual. It is **completely free to use**, the user only needs to <a href="https://diambra.ai/register/" target="_blank">register on the official website</a>.

In addition, it comes with a <a href="https://docs.diambra.ai" target="_blank">comprehensive documentation</a>, and this repository provides a **collection of examples** covering main use cases of interest **that can be run in just a few steps**.

##### Environments Main Features                                                 
                                                                                
All environments are episodic Reinforcement Learning tasks, with discrete actions (gamepad buttons) and observations composed by screen pixels plus additional numerical data (RAM values like characters health bars or characters stage side).
                                                                                
They all **support both single player (1P) as well as two players (2P) mode**, making them the perfect resource to explore all the following Reinforcement Learning subfields:

| ![standardRl](https://raw.githubusercontent.com/diambra/DIAMBRAenvironment/main/img/github.png) | ![competitiveMa](https://raw.githubusercontent.com/diambra/DIAMBRAenvironment/main/img/github.png) | ![competitieHa](https://raw.githubusercontent.com/diambra/DIAMBRAenvironment/main/img/github.png) | ![selfPlay](https://raw.githubusercontent.com/diambra/DIAMBRAenvironment/main/img/github.png) | ![imitationLearning](https://raw.githubusercontent.com/diambra/DIAMBRAenvironment/main/img/github.png) | ![humanInTheLoop](https://raw.githubusercontent.com/diambra/DIAMBRAenvironment/main/img/github.png) |
|:---:|:---:|:---:|:---:|:---:|:---:|
| Standard RL | Competitive Multi-Agent | Competitive Human-Agent | Self-Play | Imitation Learning | Human-in-the-Loop |
                                       
#### Available Games                                                            
                                                                                
Interfaced games have been selected among the most popular fighting retro-games. While sharing the same fundamental mechanics, they provide slightly different challenges, with specific features such as different type and number of characters, how to perform combos, health bars recharging, etc.
                                                                                
Whenever possible, games are released with all hidden/bonus characters unlocked.
                                                                                
Additional details can be found in the <a href="https://docs.diambra.ai/envs/games/" target="_blank">dedicated section</a> of the documentation.

| ![standardRl](https://raw.githubusercontent.com/diambra/DIAMBRAenvironment/main/img/github.png) | ![competitiveMa](https://raw.githubusercontent.com/diambra/DIAMBRAenvironment/main/img/github.png) | ![competitieHa](https://raw.githubusercontent.com/diambra/DIAMBRAenvironment/main/img/github.png) | ![selfPlay](https://raw.githubusercontent.com/diambra/DIAMBRAenvironment/main/img/github.png) | ![imitationLearning](https://raw.githubusercontent.com/diambra/DIAMBRAenvironment/main/img/github.png) | ![humanInTheLoop](https://raw.githubusercontent.com/diambra/DIAMBRAenvironment/main/img/github.png) |
|:---:|:---:|:---:|:---:|:---:|:---:|
| Dead Or Alive ++ | Street Fighter III 3rd Strike | Tekken Tag Tournament | Ultimate Mortal Kombat 3 | Samurai Showdown 5 Special | The King of Fighers '98 Ultimate Match Hero|

## Index

- **[Installation](#installation)**
- **[Quickstart](#quickstart)**
- **[AI Tournament](#ai-tournament)**
- **[References](#references)**
- **[Support, Feature Requests & Bugs Reports](#support-feature-requests--bugs-reports)**
- **[Citation](#citation)**
- **[Terms of Use](#terms-of-use)**

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

## Quickstart

![rlScheme](https://raw.githubusercontent.com/diambra/DIAMBRAenvironment/main/img/github.png)

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
settings["gameId"] = "doapp" # Game selection
settings["romsPath"] = /path/to/roms/ # Path to roms folder

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

## References

 - Documentation: <a href="https://docs.diambra.ai" target="_blank">https://docs.diambra.ai</a>
 - Website: <a href="https://diambra.ai" target="_blank">https://diambra.ai</a>
 - Discord Server: <a href="https://discord.gg/tFDS2UN5sv" target="_blank">https://discord.gg/tFDS2UN5sv</a>
 - Linkedin: <a href="https://www.linkedin.com/company/diambrav" target="_blank">https://www.linkedin.com/company/diambra</a>
 - Twitch Channel: <a href="https://www.twitch.tv/diambra_ai" target="_blank">https://www.twitch.tv/diambra_ai</a>
 - YouTube Channel: <a href="https://www.youtube.com/channel/UCMlHRxN3KtLIj1N8mKvmXDw/videos" target="_blank">https://www.youtube.com/channel/UCMlHRxN3KtLIj1N8mKvmXDw/videos</a>

## Support, Feature Requests & Bugs Reports

To receive support, use the dedicated channel in our <a href="https://discord.gg/tFDS2UN5sv" target="_blank">Discord Server</a>.

To request features or report bugs, use the <a href="https://github.com/diambra/diambraArena/issues" target="_blank">GitHub Issue Tracker</a>.

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

DIAMBRA Arena software package is subject to our <a href="https://diambra.ai/terms" target="_blank">Terms of Use</a>. By using it, you accept them in full.

###### DIAMBRA™ is a Trade Mark, © Copyright 2018 - 2022. All Right Reserved.
