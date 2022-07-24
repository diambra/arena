<img src="https://raw.githubusercontent.com/diambra/diambraArena/main/img/github.png" alt="diambra" width="100%"/>

<p align="center">
  <a href="https://docs.diambra.ai">Documentation</a> •
  <a href="https://diambra.ai/">Website</a>
</p>
<p align="center">
  <a href="https://www.linkedin.com/company/diambra">Linkedin</a> •
  <a href="https://discord.gg/tFDS2UN5sv">Discord</a> •
  <a href="https://www.twitch.tv/diambra_ai">Twitch</a> •
  <a href="https://www.youtube.com/c/diambra_ai">YouTube</a> •
  <a href="https://twitter.com/diambra_ai">Twitter</a>
</p>

# DIAMBRA Arena

DIAMBRA Arena is a software package featuring a collection of **high-quality environments for Reinforcement Learning research and experimentation**. It provides a standard interface to popular arcade emulated video games, offering a **Python API fully compliant with OpenAI Gym format**, that makes its adoption smooth and straightforward.

It **supports all major Operating Systems** (Linux, Windows and MacOS) and **can be easily installed via Python PIP**, as described in the **[installation section](#installation)** below. It is **completely free to use**, the user only needs to <a href="https://diambra.ai/register/" target="_blank">register on the official website</a>.

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

- <a href="https://diambra.ai/register/" target="_blank">Create an account on our website</a>, it requires just a few clicks and is 100% free

- Install Docker Desktop: <a href="https://docs.docker.com/desktop/install/linux-install/" target="_blank">Linux</a> | <a href="https://docs.docker.com/desktop/windows/install/" target="_blank">Windows</a> | <a href="https://docs.docker.com/desktop/mac/install/" target="_blank">MacOS</a>

- Install DIAMBRA Command Line Interface (system wide, <span style="color:#333333; font-weight:bolder;">not using</span> a virtual environment): `pip install diambra`

- Install DIAMBRA Arena (<span style="color:#333333; font-weight:bolder;">using</span> a virtual environment is strongly suggested): `pip install diambra-arena`

## Quickstart & Examples

DIAMBRA Arena usage follows the standard RL interaction framework: the agent sends an action to the environment, which process it and performs a transition accordingly, from the starting state to the new state, returning the observation and the reward to the agent to close the interaction loop. The figure below shows this typical interaction scheme and data flow.

<p align="center">
<img src="https://raw.githubusercontent.com/diambra/diambraArena/main/img/basicUsage.png" alt="rlScheme" width="75%"/>
</p>

#### Download Game ROM(s) and Check Validity

#### Base script

Running a complete episode with a random agent requires less than 20 python lines:

```python {linenos=inline}
 import diambra.arena

 env = diambra.arena.make("doapp")

 observation = env.reset()

 while True:
     env.render()

     actions = env.action_space.sample()

     observation, reward, done, info = env.step(actions)

     if done:
         observation = env.reset()
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
 - Website: <a href="https://diambra.ai" target="_blank">https://diambra.ai</a>
 - Discord: <a href="https://discord.gg/tFDS2UN5sv" target="_blank">https://discord.gg/tFDS2UN5sv</a>
 - Linkedin: <a href="https://www.linkedin.com/company/diambra" target="_blank">https://www.linkedin.com/company/diambra</a>
 - Twitch: <a href="https://www.twitch.tv/diambra_ai" target="_blank">https://www.twitch.tv/diambra_ai</a>
 - YouTube: <a href="https://www.youtube.com/c/diambra_ai" target="_blank">https://www.youtube.com/c/diambra_ai</a>
 - Twitter: <a href="https://twitter.com/diambra_ai" target="_blank">https://twitter.com/diambra_ai</a>

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
