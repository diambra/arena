import diambraArena
from diambraArena.gymUtils import showWrapObs
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
diambraKwargs["mameDiambraStepRatio"] = 6 # Number of steps performed by the game for every environment step, bounds: [1, 6]

diambraKwargs["headless"] = False # Allows to execute the environment in headless mode (for server-side executions)

diambraKwargs["showFinal"]    = False # If to show game final when game is completed

# Game-specific options (see documentation for details)
diambraKwargs["difficulty"]  = 3 # Game difficulty level
diambraKwargs["characters"]  = [["Random", "Random"], ["Random", "Random"]] # Character to be used
diambraKwargs["charOutfits"] = [2, 2] # Character outfit

# Gym options
diambraGymKwargs = {}
diambraGymKwargs["actionSpace"] = "discrete" # If to use discrete or multiDiscrete action space
diambraGymKwargs["attackButCombinations"] = True # If to use attack buttons combinations actions

# Gym wrappers options
wrappersKwargs = {}
wrappersKwargs["noOpMax"] = 0 # Number of no-Op actions to be executed at the beginning of the episode (0 by default)
wrappersKwargs["hwcObsResize"] = [128, 128, 1] # Frame resize operation spec (deactivated by default)
wrappersKwargs["normalizeRewards"] = True # If to perform rewards normalization (True by default)
wrappersKwargs["clipRewards"] = False # If to clip rewards (False by default)
wrappersKwargs["frameStack"] = 4 # Number of frames to be stacked together (1 by default)
wrappersKwargs["dilation"] = 1 # Frames interval when stacking (1 by default)
wrappersKwargs["actionsStack"] = 12 # How many past actions to stack together (1 by default)
wrappersKwargs["scale"] = True # If to scale observation numerical values (deactivated by default)
wrappersKwargs["scaleMod"] = 0 # Scaling interval (0 = [0.0, 1.0], 1 = [-1.0, 1.0])

env = diambraArena.make(envId, diambraKwargs, diambraGymKwargs, wrappersKwargs)

observation = env.reset()
showWrapObs(observation, env.nActionsStack, env.charNames)

while True:

    actions = env.action_space.sample()

    observation, reward, done, info = env.step(actions)
    showWrapObs(observation, env.nActionsStack, env.charNames)
    print("Reward: {}".format(reward))
    print("Done: {}".format(done))
    print("Info: {}".format(info))

    if done:
        observation = env.reset()
        showWrapObs(observation, env.nActionsStack, env.charNames)
        break

env.close()
