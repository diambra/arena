#!/usr/bin/env python3
import diambraArena
from diambraArena.gymUtils import showGymObs
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--envAddress', type=str, default="localhost:50051", help='diambraEngine Address')
parser.add_argument('--envId', type=str, default='0', help='envID')

opt = parser.parse_args()
print(opt)

# Settings
settings = {
    "envAddress": opt.envAddress,
    "envId": opt.envId,
}

# Additional settings
# Player side selection: P1 (left), P2 (right), Random (50% P1, 50% P2)
settings["player"] = "P2"

# Renders the environment, deactivate for speedup
settings["render"] = True

# Locks execution to 60 FPS, deactivate for speedup
settings["lockFps"] = False

# Activate game sound
settings["sound"] = settings["lockFps"] and settings["render"]

# Number of steps performed by the game for every environment step, bounds: [1, 6]
settings["stepRatio"] = 6

# Game continue logic (0.0 by default):
# - [0.0, 1.0]: probability of continuing game at game over
# - int((-inf, -1.0]): number of continues at game over before episode to be considered done
settings["continueGame"] = 0.0

# If to show game final when game is completed
settings["showFinal"] = False

# Game-specific options (see documentation for details)
# Game difficulty level
settings["difficulty"]  = 3

# Character to be used, automatically extended with "Random" for games requiring
# to select more than one character (e.g. Tekken Tag Tournament)
settings["characters"]  = [["Random"], ["Random"]]

# Character outfit
settings["charOutfits"] = [2, 2]

# Action space choice
# If to use discrete or multiDiscrete action space
settings["actionSpace"] = "discrete"

# If to use attack buttons combinations actions
settings["attackButCombination"] = True

# Environment ID, must be unique for every instance of the environment
settings["envId"] = "SinglePlayerEnv"

env = diambraArena.make("doapp", settings)

observation = env.reset()
showGymObs(observation, env.charNames)

while True:

    actions = env.action_space.sample()

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
