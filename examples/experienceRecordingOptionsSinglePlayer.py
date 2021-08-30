import diambraArena
from diambraArena.gymUtils import showWrapObs
from diambraArena.utils.diambraGamepad import diambraGamepad
import argparse
from os.path import expanduser

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
diambraEnvKwargs["mameDiambraStepRatio"] = 1 # Number of steps performed by the game for every environment step, bounds: [1, 6]

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

# Gym wrappers options
wrapperKwargs = {}
wrapperKwargs["noOpMax"] = 0 # Number of no-Op actions to be executed at the beginning of the episode (0 by default)
wrapperKwargs["hwcObsResize"] = [128, 128, 1] # Frame resize operation spec (deactivated by default)
wrapperKwargs["normalizeRewards"] = True # If to perform rewards normalization (True by default)
wrapperKwargs["clipRewards"] = False # If to clip rewards (False by default)
wrapperKwargs["frameStack"] = 4 # Number of frames to be stacked together (1 by default)
wrapperKwargs["dilation"] = 1 # Frames interval when stacking (1 by default)
wrapperKwargs["actionsStack"] = 12 # How many past actions to stack together (1 by default)
wrapperKwargs["scale"] = True # If to scale observation numerical values (deactivated by default)
wrapperKwargs["scaleMod"] = 0 # Scaling interval (0 = [0.0, 1.0], 1 = [-1.0, 1.0])

# Gym experience recording wrapper kwargs
homeDir = expanduser("~")
expRecKwargs = {}
expRecKwargs["userName"] = "Alex" # Username
expRecKwargs["filePath"] = os.path.join(homeDir, "diambraArena/expRecordings",
                                        diambraEnvKwargs["gameId"]) # Path where to save recorderd experience
expRecKwargs["ignoreP2"] = 0 # If to ignore P2 experience (useful when collecting
                             # only human experience while playing as a human against a RL agent)

env = diambraArena.make(envId, diambraEnvKwargs, diambraGymKwargs, wrapperKwargs,
                        expRecKwargs)

# GamePad(s) initialization
gamepad = diambraGamepad(env.actionList())
gamepad.start()

observation = env.reset()

while True:

    actions = gamepad.getActions()

    observation, reward, done, info = env.step(actions)
    showWrapObs(observation, env.charNames, 1, False)

    if done:
        observation = env.reset()
        showWrapObs(observation, env.charNames, 1, False)
        break

env.close()
