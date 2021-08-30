import diambraArena
from diambraArena.gymUtils import showGymObs
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--romsPath', type=str, required=True, help='Absolute path to roms')
opt = parser.parse_args()
print(opt)

# Mandatory parameters
diambraEnvKwargs = {}
diambraEnvKwargs["gameId"]   = "doapp" # Game selection
diambraEnvKwargs["romsPath"] = opt.romsPath # Path to roms folder
envId = "TestEnv" # This ID must be unique for every instance of the environment

# Additional game options
diambraEnvKwargs["player"] = "Random" # Player side selection: P1 (left), P2 (right), Random (50% P1, 50% P2)

# Game continue logic (0.0 by default):
# - [0.0, 1.0]: probability of continuing game at game over
# - int((-inf, -1.0]): number of continues at game over before episode to be considered done
diambraKwargs["continueGame"] = -1.0

diambraEnvKwargs["render"] = True # Renders the environment, deactivate for speedup
diambraEnvKwargs["lockFps"] = False # Locks to 60 FPS, deactivate for speedup
diambraEnvKwargs["sound"] = diambraEnvKwargs["lockFps"] and diambraEnvKwargs["render"] # Activate game sound
diambraEnvKwargs["mameDiambraStepRatio"] = 6 # Number of steps performed by the game for every environment step, bounds: [1, 6]

diambraEnvKwargs["headless"] = False # Allows to execute the environment in headless mode (for server-side executions)

diambraKwargs["showFinal"]    = False # If to show game final when game is completed

# Game-specific options (see documentation for details)
diambraEnvKwargs["difficulty"]  = 3 # Game difficulty level
diambraEnvKwargs["characters"]  = [["Random", "Random"], ["Random", "Random"]] # Character to be used
diambraEnvKwargs["charOutfits"] = [2, 2] # Character outfit

# Gym options
diambraGymKwargs = {}
diambraGymKwargs["actionSpace"] = "discrete" # If to use discrete or multiDiscrete action space
diambraGymKwargs["attackButCombinations"] = True # If to use attack buttons combinations actions

env = diambraArena.make(envId, diambraEnvKwargs, diambraGymKwargs)

observation = env.reset()

while True:

    actions = env.action_space.sample()

    observation, reward, done, info = env.step(actions)
    showGymObs(observation, env.charNames)

    if done:
        observation = env.reset()
        showGymObs(observation, env.charNames)
        break

env.close()
