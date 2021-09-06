import diambraArena
from diambraArena.gymUtils import showGymObs
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
diambraKwargs["player"] = "Random" # Player side selection: P1 (left), P2 (right), Random (50% P1, 50% P2)

# Game continue logic (0.0 by default):
# - [0.0, 1.0]: probability of continuing game at game over
# - int((-inf, -1.0]): number of continues at game over before episode to be considered done
diambraKwargs["continueGame"] = -1.0

diambraKwargs["render"] = True # Renders the environment, deactivate for speedup
diambraKwargs["lockFps"] = False # Locks to 60 FPS, deactivate for speedup
diambraKwargs["sound"] = diambraKwargs["lockFps"] and diambraKwargs["render"] # Activate game sound
diambraKwargs["stepRatio"] = 6 # Number of steps performed by the game for every environment step, bounds: [1, 6]

diambraKwargs["headless"] = False # Allows to execute the environment in headless mode (for server-side executions)

diambraKwargs["showFinal"]    = False # If to show game final when game is completed

# Game-specific options (see documentation for details)
diambraKwargs["difficulty"]  = 3 # Game difficulty level
diambraKwargs["characters"]  = [["Random", "Random"], ["Random", "Random"]] # Character to be used
diambraKwargs["charOutfits"] = [2, 2] # Character outfit

env = diambraArena.make(envId, diambraKwargs)

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
