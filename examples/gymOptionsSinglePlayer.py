import diambraArena
from diambraArena.gymUtils import showGymObs
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--romsPath', type=str, required=False, help='Absolute path to roms')
opt = parser.parse_args()
print(opt)

# Mandatory parameters
settings = {}
settings["gameId"]   = "doapp" # Game selection
if opt.romsPath is not None:
    settings["romsPath"] = opt.romsPath # Path to roms folder
envId = "TestEnv" # This ID must be unique for every instance of the environment

# Additional game options
settings["player"] = "Random" # Player side selection: P1 (left), P2 (right), Random (50% P1, 50% P2)

# Game continue logic (0.0 by default):
# - [0.0, 1.0]: probability of continuing game at game over
# - int((-inf, -1.0]): number of continues at game over before episode to be considered done
settings["continueGame"] = -1.0

settings["render"] = True # Renders the environment, deactivate for speedup
settings["lockFps"] = False # Locks to 60 FPS, deactivate for speedup
settings["sound"] = settings["lockFps"] and settings["render"] # Activate game sound
settings["stepRatio"] = 6 # Number of steps performed by the game for every environment step, bounds: [1, 6]

settings["headless"] = False # Allows to execute the environment in headless mode (for server-side executions)

settings["showFinal"]    = False # If to show game final when game is completed

# Game-specific options (see documentation for details)
settings["difficulty"]  = 3 # Game difficulty level
settings["characters"]  = [["Random", "Random"], ["Random", "Random"]] # Character to be used
settings["charOutfits"] = [2, 2] # Character outfit

# Action space choice
settings["actionSpace"]          = "discrete" # If to use discrete or multiDiscrete action space
settings["attackButCombination"] = True # If to use attack buttons combinations actions

env = diambraArena.make(envId, settings)

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
