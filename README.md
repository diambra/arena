<img src="https://raw.githubusercontent.com/diambra/diambraArena/main/img/github.png" alt="diambra" width="100%"/>

<p align="center">
  <a href="https://docs.diambra.ai">Documentation</a> •
  <a href="https://diambra.ai/">Website</a>
</p>
<p align="center">
  <a href="https://www.linkedin.com/company/diambra">Linkedin</a> •
  <a href="https://discord.gg/tFDS2UN5sv">Discord</a> •
  <a href="https://www.twitch.tv/diambra_ai">Twitch</a> •
  <a href="https://www.youtube.com/c/diambra_ai">YouTube</a>
</p>

# DIAMBRA Arena

DIAMBRA Arena is a software package featuring a collection of **high-quality environments for Reinforcement Learning research and experimentation**. It acts as an interface towards popular arcade emulated video games, offering a **Python API fully compliant with OpenAI Gym standard**, that makes its adoption smooth and straightforward.

It **supports all major Operating Systems: Linux, Windows and MacOS**, most of them via Docker, with a step by step installation guide available in this manual. It is **completely free to use**, the user only needs to <a href="https://diambra.ai/register/" target="_blank">register on the official website</a>.

In addition, it comes with a <a href="https://docs.diambra.ai" target="_blank">comprehensive documentation</a>, and this repository provides a **collection of examples** covering main use cases of interest **that can be run in just a few steps**.

#### Main Features                                                 
                                                                                
All environments are episodic Reinforcement Learning tasks, with discrete actions (gamepad buttons) and observations composed by screen pixels plus additional numerical data (RAM values like characters health bars or characters stage side).
                                                                                
They all **support both single player (1P) as well as two players (2P) mode**, making them the perfect resource to explore all the following Reinforcement Learning subfields:

| <img src="https://raw.githubusercontent.com/diambra/diambraArena/main/img/AIvsCOM.png" alt="standardRl" width="125"/> | <img src="https://raw.githubusercontent.com/diambra/diambraArena/main/img/AIvsAI.png" alt="competitiveMa" width="125"/> | <img src="https://raw.githubusercontent.com/diambra/diambraArena/main/img/AIvsHUM.png" alt="competitiveHa" width="125"/> | <img src="https://raw.githubusercontent.com/diambra/diambraArena/main/img/SP.png" alt="selfPlay" width="125"/> | <img src="https://raw.githubusercontent.com/diambra/diambraArena/main/img/IL.png" alt="imitationLearning" width="125"/> | <img src="https://raw.githubusercontent.com/diambra/diambraArena/main/img/HITL.png" alt="humanInTheLoop" width="125"/> |
|:---:|:---:|:---:|:---:|:---:|:---:|
| Standard RL | Competitive<br>Multi-Agent | Competitive<br> Human-Agent | Self-Play | Imitation Learning | Human-in-the-Loop |
                                       
#### Available Games
                                                                                
Interfaced games have been selected among the most popular fighting retro-games. While sharing the same fundamental mechanics, they provide slightly different challenges, with specific features such as different type and number of characters, how to perform combos, health bars recharging, etc.
                                                                                
Whenever possible, games are released with all hidden/bonus characters unlocked.
                                                                                
Additional details can be found in the <a href="https://docs.diambra.ai/envs/games/" target="_blank">dedicated section</a> of our Documentation.

| <img src="https://raw.githubusercontent.com/diambra/diambraArena/main/img/doapp.jpg" alt="doapp" width="125"/> | <img src="https://raw.githubusercontent.com/diambra/diambraArena/main/img/sfiii3n.jpg" alt="sfiii3n" width="125"/> | <img src="https://raw.githubusercontent.com/diambra/diambraArena/main/img/tektagt.jpg" alt="tektagt" width="125"/> | <img src="https://raw.githubusercontent.com/diambra/diambraArena/main/img/umk3.jpg" alt="umk3" width="125"/> | <img src="https://raw.githubusercontent.com/diambra/diambraArena/main/img/samsh5sp.jpg" alt="samsh6sp" width="125"/> | <img src="https://raw.githubusercontent.com/diambra/diambraArena/main/img/kof98umh.jpg" alt="kof98umh" width="125"/> |
|:---:|:---:|:---:|:---:|:---:|:---:|
| Dead<br>Or<br>Alive ++ | Street<br>Fighter III<br>3rd Strike | Tekken Tag<br>Tournament | Ultimate<br>Mortal<br>Kombat 3 | Samurai<br>Showdown<br>5 Special | The King of<br>Fighers '98<br>Ultimate<br>Match Hero|

**Many more are coming soon...**

## Index

- **[Installation](#installation)**
- **[Quickstart & Examples](#quickstart--examples)**
- **[AI Tournaments](#ai-tournaments)**
- **[References](#references)**
- **[Support, Feature Requests & Bugs Reports](#support-feature-requests--bugs-reports)**
- **[Citation](#citation)**
- **[Terms of Use](#terms-of-use)**

## Installation

DIAMBRA Arena runs on all major Operating Systems: Linux, Windows and MacOS. It is natively supported on Linux Ubuntu 18.04 or newer and Linux Mint 19 or newer, where it can be installed directly from sources. For all other options (different Linux distributions, Windows and MacOS), it leverages Docker technology.

Docker installation is quick and controlled, with equal (if not better) performances in terms of environment execution speed, when compared with installation from source. It even allows, on every OS, to run all environments with rendering active, showing game frames on screen in real time.

The installation takes only a few steps, **<a href="https://docs.diambra.ai/installation/" target="_blank">refer to the dedicated section</a> of our Documentation** where they are clearly explained.

#### Prerequisites

In order to use DIAMBRA Arena, it is needed to:
 - Have an active internet connection
 - **<a href="https://diambra.ai/register/" target="_blank">Create an account on our website</a>**, it requires just a few clicks and is 100% free

Credentials (email/user id and password) will be asked at the first environment execution.

## Quickstart & Examples

DIAMBRA Arena usage follows the standard RL interaction framework: the agent sends an action to the environment, which process it and performs a transition accordingly, from the starting state to the new state, returning the observation and the reward to the agent to close the interaction loop. The figure below shows this typical interaction scheme and data flow.

<p align="center">
<img src="https://raw.githubusercontent.com/diambra/diambraArena/main/img/basicUsage.png" alt="rlScheme" width="75%"/>
</p>

The shortest snippet for a complete basic execution of an environment consists of just a few lines of code, and is presented in the code block below:

```python
import diambraArena

# Mandatory settings
settings = {}
settings["gameId"] = "doapp" # Game selection
settings["romsPath"] = "/path/to/roms/" # Path to roms folder

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

### Examples

The `examples/` folder contains ready to use scripts representing the most important use-cases, in particular:
 - Single Player Environment
 - Multi Player Environment
 - Wrappers Options
 - Human Experience Recorder
 - Imitation Learning

These examples show how to leverage both single and two players modes, how to set up environment wrappers specifying all their options, how to record human expert demonstrations and how to load them to apply imitation learning. They can be used as templates and starting points to explore all the features of the software package.

<img src="https://raw.githubusercontent.com/diambra/DIAMBRAenvironment/main/img/github.gif" alt="diambraGif" width="100%"/>

## AI Tournaments

We are about to launch our AI Tournaments Platform, where every coder will be able to train his agents and compete.
There will be one-to-one fights against other agents, challenges to collect accolades & bages, and matches versus human players.

**<a href="https://diambra.ai/register/" target="_blank">Join us to become an early member!</a>**

<img src="https://raw.githubusercontent.com/diambra/DIAMBRAenvironment/main/img/WideFlyer.jpg" alt="diambraAITournament" width="100%"/>

Our very first AI Tournament **has been an amazing experience!** Participants trained an AI algorithm to effectively play Dead Or Alive++. The three best algorithms participated in the final event and **competed for the 1400 CHF prize.**

## References

 - Documentation: <a href="https://docs.diambra.ai" target="_blank">https://docs.diambra.ai</a>
 - Docker Repository: <a href="https://hub.docker.com/r/diambra/diambra-arena" target="_blank">https://hub.docker.com/r/diambra/diambra-arena</a>
 - Website: <a href="https://diambra.ai" target="_blank">https://diambra.ai</a>
 - Discord Server: <a href="https://discord.gg/tFDS2UN5sv" target="_blank">https://discord.gg/tFDS2UN5sv</a>
 - Linkedin: <a href="https://www.linkedin.com/company/diambrav" target="_blank">https://www.linkedin.com/company/diambra</a>
 - Twitch Channel: <a href="https://www.twitch.tv/diambra_ai" target="_blank">https://www.twitch.tv/diambra_ai</a>
 - YouTube Channel: <a href="https://www.youtube.com/c/diambra_ai" target="_blank">https://www.youtube.com/c/diambra_ai</a>

## Support, Feature Requests & Bugs Reports

To receive support, use the dedicated channel in our <a href="https://discord.gg/tFDS2UN5sv" target="_blank">Discord Server</a>.

To request features or report bugs, use the <a href="https://github.com/diambra/diambraArena/issues" target="_blank">GitHub Issue Tracker</a>.

## Citation
```
  @misc{diambra2022
    author = {DIAMBRA Team},
    title = {DIAMBRA Arena: built with OpenAI Gym Python interface, easy to use, transforms popular video games into Reinforcement Learning environments.},
    year = {2022},
    howpublished = {\url{https://github.com/diambra/diambraArena}},
  }
```

## Terms of Use

DIAMBRA Arena software package is subject to our <a href="https://diambra.ai/terms" target="_blank">Terms of Use</a>. By using it, you accept them in full.

###### DIAMBRA™ is a Trade Mark, © Copyright 2018 - 2022. All Right Reserved.
