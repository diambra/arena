<img src="https://raw.githubusercontent.com/diambra/arena/main/img/github.jpg" alt="diambra" width="100%"/>

<p align="center">
  <a href="https://docs.diambra.ai">Documentation</a> •
  <a href="https://diambra.ai/">Website</a>
</p>
<p align="center">
  <a href="https://www.linkedin.com/company/diambra">Linkedin</a> •
  <a href="https://diambra.ai/discord">Discord</a> •
  <a href="https://www.twitch.tv/diambra_ai">Twitch</a> •
  <a href="https://www.youtube.com/c/diambra_ai">YouTube</a> •
  <a href="https://twitter.com/diambra_ai">Twitter</a>
</p>

<p align="center">
<a href="https://arxiv.org/abs/2210.10595"><img src="https://img.shields.io/badge/paper-arXiv:2210.10595-B31B1B?logo=arxiv" alt="Paper"/></a>
</p>
<p align="center">
<a href="https://github.com/diambra/arena/actions/workflows/test.yaml"><img src="https://img.shields.io/github/actions/workflow/status/diambra/arena/test.yaml?label=arena%20tests&logo=github" alt="Arena Test"/></a>
<a href="https://github.com/diambra/arena/actions/workflows/test_agents.yaml"><img src="https://img.shields.io/github/actions/workflow/status/diambra/arena/test_agents.yaml?label=agents%20tests&logo=github" alt="Agents Test"/></a>
<a href="https://github.com/diambra/arena/tags"><img src="https://img.shields.io/github/v/tag/diambra/arena?label=latest%20tag&logo=github" alt="Latest Tag"/></a>
<a href="https://pypi.org/project/diambra-arena/"><img src="https://img.shields.io/pypi/v/diambra-arena?logo=pypi" alt="Pypi version"/></a>
</p>
<p align="center">
<a href="https://docs.diambra.ai/#installation"><img src="https://img.shields.io/badge/supported%20os-linux%20%7C%20win%20%7C%20macOS-blue?logo=docker" alt="Supported OS"/></a>
<a href="https://docs.diambra.ai/"><img src="https://img.shields.io/github/last-commit/diambra/docs/main?label=docs%20last%20update&logo=readthedocs" alt="Last Docs Update"/></a>
</p>



# DIAMBRA Arena

## Index

- **[Overview](#overview)**
- **[Competition Platform](#competition-platform)**
- **[Installation](#installation)**
- **[Quickstart & Examples](#quickstart--examples)**
- **[Reinforcement Learning Libs Compatibility](#reinforcement-learning-libs-compatibility)**
- **[References](#references)**
- **[Support, Feature Requests & Bugs Reports](#support-feature-requests--bugs-reports)**
- **[Citation](#citation)**
- **[Terms of Use](#terms-of-use)**

## Overview

DIAMBRA Arena is a software package featuring a collection of **high-quality environments for Reinforcement Learning research and experimentation**. It provides a standard interface to popular arcade emulated video games, offering a **Python API fully compliant with OpenAI Gym/Gymnasium format**, that makes its adoption smooth and straightforward.

It **supports all major Operating Systems** (Linux, Windows and MacOS) and **can be easily installed via Python PIP**, as described in the **[installation section](#installation)** below. It is **completely free to use**, the user only needs to <a href="https://diambra.ai/register/" target="_blank">register on the official website</a>.

In addition, it comes with a <a href="https://docs.diambra.ai" target="_blank">comprehensive documentation</a>, and this repository provides a **collection of examples** covering main use cases of interest **that can be run in just a few steps**.

#### Main Features

All environments are episodic Reinforcement Learning tasks, with discrete actions (gamepad buttons) and observations composed by screen pixels plus specific RAM states (like characters health bars or characters stage side).

They all **support both single player (1P) as well as two players (2P) mode**, making them the perfect resource to explore all the following Reinforcement Learning subfields:

| <img src="https://raw.githubusercontent.com/diambra/arena/main/img/AIvsCOM.png" alt="standardRl" width="125"/> | <img src="https://raw.githubusercontent.com/diambra/arena/main/img/AIvsAI.png" alt="competitiveMa" width="125"/> | <img src="https://raw.githubusercontent.com/diambra/arena/main/img/AIvsHUM.png" alt="competitiveHa" width="125"/> | <img src="https://raw.githubusercontent.com/diambra/arena/main/img/SP.png" alt="selfPlay" width="125"/> | <img src="https://raw.githubusercontent.com/diambra/arena/main/img/IL.png" alt="imitationLearning" width="125"/> | <img src="https://raw.githubusercontent.com/diambra/arena/main/img/HITL.png" alt="humanInTheLoop" width="125"/> |
| :-------------------------------------------------------------------------------------------------------------------: | :---------------------------------------------------------------------------------------------------------------------: | :----------------------------------------------------------------------------------------------------------------------: | :------------------------------------------------------------------------------------------------------------: | :---------------------------------------------------------------------------------------------------------------------: | :--------------------------------------------------------------------------------------------------------------------: |
|                                                      Standard RL                                                      |                                               Competitive<br>Multi-Agent                                                |                                               Competitive<br> Human-Agent                                                |                                                   Self-Play                                                    |                                                   Imitation Learning                                                    |                                                   Human-in-the-Loop                                                    |

#### Available Games

Interfaced games have been selected among the most popular fighting retro-games. While sharing the same fundamental mechanics, they provide slightly different challenges, with specific features such as different type and number of characters, how to perform combos, health bars recharging, etc.

Whenever possible, games are released with all hidden/bonus characters unlocked.

Additional details can be found in the <a href="https://docs.diambra.ai/envs/games/" target="_blank">dedicated section</a> of our Documentation.

| <img src="https://raw.githubusercontent.com/diambra/arena/main/img/doapp.jpg" alt="doapp" width="125"/> | <img src="https://raw.githubusercontent.com/diambra/arena/main/img/sfiii3n.jpg" alt="sfiii3n" width="125"/> | <img src="https://raw.githubusercontent.com/diambra/arena/main/img/tektagt.jpg" alt="tektagt" width="125"/> | <img src="https://raw.githubusercontent.com/diambra/arena/main/img/umk3.jpg" alt="umk3" width="125"/> | <img src="https://raw.githubusercontent.com/diambra/arena/main/img/samsh5sp.jpg" alt="samsh6sp" width="125"/> | <img src="https://raw.githubusercontent.com/diambra/arena/main/img/kof98umh.jpg" alt="kof98umh" width="125"/> |
| :------------------------------------------------------------------------------------------------------------: | :----------------------------------------------------------------------------------------------------------------: | :----------------------------------------------------------------------------------------------------------------: | :----------------------------------------------------------------------------------------------------------: | :------------------------------------------------------------------------------------------------------------------: | :------------------------------------------------------------------------------------------------------------------: |
|                                             Dead<br>Or<br>Alive ++                                             |                                        Street<br>Fighter III<br>3rd Strike                                         |                                              Tekken Tag<br>Tournament                                              |                                        Ultimate<br>Mortal<br>Kombat 3                                        |                                           Samurai<br>Showdown<br>5 Special                                           |                                 The King of<br>Fighers '98<br>Ultimate<br>Match Hero                                 |

**Many more are coming soon...**

## Competition Platform

<img src="https://raw.githubusercontent.com/diambra/.github/master/img/platform.jpg" alt="DIAMBRA Competition Platform" width="100%"/>

Our competition platform allows you to submit your agents and compete with other coders around the globe in epic video games tournaments!

It features a public global leaderboard where users are ranked by the best score achieved by their agents in our different environments.

It also offers you the possibility to unlock cool achievements depending on the performances of your agent.

Submitted agents are evaluated and their episodes are streamed on our Twitch channel.

We aimed at making the submission process as smooth as possible, **<a href="https://diambra.ai/register/" target="_blank">join us and try it now!</a>**

## Installation

- <a href="https://diambra.ai/register/" target="_blank">Create an account on our website</a>, it requires just a few clicks and is 100% free

- Install Docker Desktop: <a href="https://docs.docker.com/desktop/install/linux-install/" target="_blank">Linux</a> | <a href="https://docs.docker.com/desktop/windows/install/" target="_blank">Windows</a> | <a href="https://docs.docker.com/desktop/mac/install/" target="_blank">MacOS</a>

- Install DIAMBRA Command Line Interface: `python3 -m pip install diambra`

- Install DIAMBRA Arena: `python3 -m pip install diambra-arena`

**Using a virtual environment to isolate your python packages installation is strongly suggested**

## Quickstart & Examples

DIAMBRA Arena usage follows the standard RL interaction framework: the agent sends an action to the environment, which process it and performs a transition accordingly, from the starting state to the new state, returning the observation and the reward to the agent to close the interaction loop. The figure below shows this typical interaction scheme and data flow.

<p align="center">
<img src="https://raw.githubusercontent.com/diambra/arena/main/img/basicUsage.png" alt="rlScheme" width="75%"/>
</p>

#### Download Game ROM(s) and Check Validity

Check out available games:

```
diambra arena list-roms
```

Output extract:

```shell
[...]
 Title: Dead Or Alive ++ - GameId: doapp
   Difficulty levels: Min 1 - Max 4
   SHA256 sum: d95855c7d8596a90f0b8ca15725686567d767a9a3f93a8896b489a160e705c4e
   Original ROM name: doapp.zip
   Search keywords: ['DEAD OR ALIVE ++ [JAPAN]', 'dead-or-alive-japan', '80781', 'wowroms']
   Characters list: ['Kasumi', 'Zack', 'Hayabusa', 'Bayman', 'Lei-Fang', 'Raidou', 'Gen-Fu', 'Tina', 'Bass', 'Jann-Lee', 'Ayane']
[...]
```

Search ROMs on the web using **Search Keywords** provided by the game list command reported above. **Pay attention, follow game-specific notes reported there, and store all ROMs in the same folder, whose absolute path will be referred in the following as** `your/roms/local/path`.

**Specific game ROM files are required, check validity of the downloaded ROMs:**

```
diambra arena check-roms your/roms/local/path/romFileName.zip
```

The output for a valid ROM file would look like:

```
Correct ROM file for Dead Or Alive ++, sha256 = d95855c7d8596a90f0b8ca15725686567d767a9a3f93a8896b489a160e705c4e
```

**Make sure to check out our <a href="https://diambra.ai/terms" target="_blank">Terms of Use</a>, and in particular Section 7. By using the software, you accept them in full.</span>**

#### Base script

Running a complete episode with a random agent requires about 10 python lines:

```python {linenos=inline}
 import diambra.arena

 env = diambra.arena.make("doapp", render_mode="human")
 observation, info = env.reset(seed=42)

 while True:
     env.render()

     actions = env.action_space.sample()
     observation, reward, terminated, truncated, info = env.step(actions)

     if terminated or truncated:
         observation, info = env.reset()
         break

 env.close()
```

To execute the script run:

```
diambra run -r your/roms/local/path python script.py
```

Additional details and use cases are provided in the <a href="https://docs.diambra.ai/gettingstarted/" target="_blank">Getting Started</a> section of the documentation.

### Examples

The `examples/` folder contains ready to use scripts representing the most important use-cases, in particular:

- Single Player Environment
- Multi Player Environment
- Wrappers Options
- Episode Recording
- Episode Data Loader

These examples show how to leverage both single and two players modes, how to set up environment wrappers specifying all their options, how to record human expert demonstrations and how to load them to apply imitation learning. They can be used as templates and starting points to explore all the features of the software package.

<img src="https://raw.githubusercontent.com/diambra/arena/main/img/github.gif" alt="diambraGif" width="100%"/>

## Reinforcement Learning Libs Compatibility

DIAMBRA Arena is built to maximize compatibility will all major Reinforcement Learning libraries. It natively provides interfaces with the two most import packages: Stable Baselines 3 and Ray RLlib, while Stable Baselines is also available but deprecated. Their usage is illustrated in detail in the <a href="https://docs.diambra.ai/handsonreinforcementlearning/" target="_blank">documentation</a> and in the <a href="https://github.com/diambra/agents" target="_blank">DIAMBRA Agents</a>  repository. It can easily be interfaced with any other package in a similar way.

Native interfaces, installed with the specific options listed below, are tested with the following versions:

- Stable Baselines 3 | `pip install diambra-arena[stable-baselines3]` (<a href="https://stable-baselines3.readthedocs.io/en/master/index.html" target="_blank">Docs</a> - <a href="https://github.com/DLR-RM/stable-baselines3" target="_blank">GitHub</a> - <a href="https://pypi.org/project/stable-baselines3/" target="_blank">Pypi</a>): 2.1.*
- Ray RLlib | `pip install diambra-arena[ray-rllib]` (<a href="https://docs.ray.io/en/latest/index.html" target="_blank">Docs</a> - <a href="https://github.com/ray-project/ray" target="_blank">GitHub</a> - <a href="https://pypi.org/project/ray/" target="_blank">Pypi</a>): 2.7.*
- Stable Baselines | `pip install diambra-arena[stable-baselines]` (<a href="https://stable-baselines.readthedocs.io/en/master/index.html" target="_blank">Docs</a> - <a href="https://github.com/hill-a/stable-baselines" target="_blank">GitHub</a> - <a href="https://pypi.org/project/stable-baselines/" target="_blank">Pypi</a>): 2.10.2

## References

- Documentation: <a href="https://docs.diambra.ai" target="_blank">https://docs.diambra.ai</a>
- Paper: <a href="https://arxiv.org/abs/2210.10595" target="_blank">https://arxiv.org/abs/2210.10595</a>
- Website: <a href="https://diambra.ai" target="_blank">https://diambra.ai</a>
- Discord: <a href="https://diambra.ai/discord" target="_blank">https://diambra.ai/discord</a>
- Linkedin: <a href="https://www.linkedin.com/company/diambra" target="_blank">https://www.linkedin.com/company/diambra</a>
- Twitch: <a href="https://www.twitch.tv/diambra_ai" target="_blank">https://www.twitch.tv/diambra_ai</a>
- YouTube: <a href="https://www.youtube.com/c/diambra_ai" target="_blank">https://www.youtube.com/c/diambra_ai</a>
- Twitter: <a href="https://twitter.com/diambra_ai" target="_blank">https://twitter.com/diambra_ai</a>

## Support, Feature Requests & Bugs Reports

To receive support, use the dedicated channel in our <a href="https://diambra.ai/discord" target="_blank">Discord Server</a>.

To request features or report bugs, use the <a href="https://github.com/diambra/arena/issues" target="_blank">GitHub Issue Tracker</a>.

## Citation

Paper: <a href="https://arxiv.org/abs/2210.10595" target="_blank">https://arxiv.org/abs/2210.10595</a>

```LaTex
@article{Palmas22,
    author = {{Palmas}, Alessandro},
    title = "{DIAMBRA Arena: a New Reinforcement Learning Platform for Research and Experimentation}",
    journal = {arXiv e-prints},
    keywords = {reinforcement learning, transfer learning, multi-agent, games},
    year = 2022,
    month = oct,
    eid = {arXiv:2210.10595},
    pages = {arXiv:2210.10595},
    archivePrefix = {arXiv},
    eprint = {2210.10595},
    primaryClass = {cs.AI}
 }
```

## Terms of Use

DIAMBRA Arena software package is subject to our <a href="https://diambra.ai/terms" target="_blank">Terms of Use</a>. By using it, you accept them in full.

###### DIAMBRA, Inc. © Copyright 2018-2023. All Rights Reserved.
