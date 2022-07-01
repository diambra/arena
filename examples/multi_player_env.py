#!/usr/bin/env python3
import diambra.arena
from diambra.arena.utils.gym_utils import show_gym_obs
import numpy as np

# Environment Settings
settings = {}

# 2 Players game
settings["player"] = "P1P2"

# If to use discrete or multiDiscrete action space
settings["action_space"] = ["discrete", "discrete"]

# If to use attack buttons combinations actions
settings["attack_but_combination"] = [True, True]

env = diambra.arena.make("doapp", settings)

observation = env.reset()
show_gym_obs(observation, env.char_names)

while True:

    actions = env.action_space.sample()
    actions = np.append(actions["P1"], actions["P2"])

    observation, reward, done, info = env.step(actions)
    show_gym_obs(observation, env.char_names)
    print("Reward: {}".format(reward))
    print("Done: {}".format(done))
    print("Info: {}".format(info))

    if done:
        observation = env.reset()
        show_gym_obs(observation, env.char_names)
        break

env.close()
