#!/usr/bin/env python3
import diambraArena
from diambraArena.gymUtils import showGymObs
import numpy as np

# Environment Settings
settings = {}

# 2 Players game
settings["player"] = "P1P2"

# If to use discrete or multiDiscrete action space
settings["actionSpace"] = ["discrete", "discrete"]

# If to use attack buttons combinations actions
settings["attackButCombination"] = [True, True]

env = diambraArena.make("doapp", settings)

observation = env.reset()
showGymObs(observation, env.charNames)

while True:

    actions = env.action_space.sample()
    actions = np.append(actions["P1"], actions["P2"])

    observation, reward, done, info = env.step(actions)
    showGymObs(observation, env.charNames)
    print("Reward: {}".format(reward))
    print("Done: {}".format(done))
    print("Info: {}".format(info))

    if done:
        observation = env.reset()
        showGymObs(observation, env.charNames)
        break

env.close()
