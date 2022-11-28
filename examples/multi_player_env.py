#!/usr/bin/env python3
import diambra.arena
import numpy as np

# Environment Settings
settings = {}

# 2 Players game
settings["player"] = "P1P2"

# Characters to be used, automatically extended with "Random" for games
# required to select more than one character (e.g. Tekken Tag Tournament)
settings["characters"] = ("Random", "Random")

# Characters outfit
settings["char_outfits"] = (2, 2)

# If to use discrete or multi_discrete action space
settings["action_space"] = ("discrete", "discrete")

# If to use attack buttons combinations actions
settings["attack_but_combination"] = (True, True)

env = diambra.arena.make("doapp", settings)

observation = env.reset()
env.show_obs(observation)

while True:

    actions = env.action_space.sample()
    actions = np.append(actions["P1"], actions["P2"])
    print("Actions: {}".format(actions))

    observation, reward, done, info = env.step(actions)
    env.show_obs(observation)
    print("Reward: {}".format(reward))
    print("Done: {}".format(done))
    print("Info: {}".format(info))

    if done:
        observation = env.reset()
        env.show_obs(observation)
        break

env.close()
