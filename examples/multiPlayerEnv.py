import diambraArena
from diambraArena.gymUtils import showGymObs
import numpy as np
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--romsPath', type=str, required=False, help='Absolute path to roms')
opt = parser.parse_args()
print(opt)

# Mandatory settings
settings = {}
if opt.romsPath is not None:
    # Path to roms folder
    settings["romsPath"] = opt.romsPath

# Additional settings
# 2 Players game
settings["player"] = "P1P2"

# Action space choice
# If to use discrete or multiDiscrete action space
settings["actionSpace"] = ["discrete", "discrete"]

# If to use attack buttons combinations actions
settings["attackButCombination"] = [True, True]

# Envid
settings["envId"] = "MultiPlayerEnv"

env = diambraArena.make("doapp", settings)

observation = env.reset()
showGymObs(observation, env.charNames, env.partnerNames)

while True:

    actions = env.action_space.sample()
    actions = np.append(actions["P1"], actions["P2"])

    observation, reward, done, info = env.step(actions)
    showGymObs(observation, env.charNames, env.partnerNames)
    print("Reward: {}".format(reward))
    print("Done: {}".format(done))
    print("Info: {}".format(info))

    if done:
        observation = env.reset()
        showGymObs(observation, env.charNames, env.partnerNames)
        break

env.close()
