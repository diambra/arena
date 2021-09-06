import diambraArena
from diambraArena.gymUtils import showGymObs
import numpy as np
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--romsPath', type=str, required=True, help='Absolute path to roms')
opt = parser.parse_args()
print(opt)

# Mandatory parameters
diambraKwargs = {}
diambraKwargs["gameId"]   = "doapp" # Game selection
diambraKwargs["romsPath"] = opt.romsPath # Path to roms folder
envId = "TestEnv" # This ID must be unique for every instance of the environment

# Additional game options
diambraKwargs["player"] = "P1P2" # 2 Players game

diambraKwargs["render"] = True # Renders the environment, deactivate for speedup
diambraKwargs["lockFps"] = False # Locks to 60 FPS, deactivate for speedup
diambraKwargs["sound"] = diambraKwargs["lockFps"] and diambraKwargs["render"] # Activate game sound
diambraKwargs["stepRatio"] = 6 # Number of steps performed by the game for every environment step, bounds: [1, 6]

diambraKwargs["headless"] = False # Allows to execute the environment in headless mode (for server-side executions)

# Game-specific options (see documentation for details)
diambraKwargs["difficulty"]  = 3 # Game difficulty level
diambraKwargs["characters"]  = [["Random", "Random"], ["Random", "Random"]] # Character to be used
diambraKwargs["charOutfits"] = [2, 2] # Character outfit

env = diambraArena.make(envId, diambraKwargs)

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
