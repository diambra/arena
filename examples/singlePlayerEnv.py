import diambraArena
from diambraArena.gymUtils import showGymObs
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--romsPath', type=str, required=False, help='Absolute path to roms')
opt = parser.parse_args()
print(opt)

# Mandatory settings
settings = {}

# Game selection
settings["gameId"] = "doapp"

if opt.romsPath is not None:
    # Path to roms folder
    settings["romsPath"] = opt.romsPath

# Additional settings
# Player side selection: P1 (left), P2 (right), Random (50% P1, 50% P2)
settings["player"] = "Random"

# Renders the environment, deactivate for speedup
settings["render"] = True

# Locks execution to 60 FPS, deactivate for speedup
settings["lockFps"] = False

# Activate game sound
settings["sound"] = settings["lockFps"] and settings["render"]

# Number of steps performed by the game for every environment step, bounds: [1, 6]
settings["stepRatio"] = 6

# Allows to execute the environment in headless mode (for server-side executions)
settings["headless"] = False

# Game continue logic (0.0 by default):
# - [0.0, 1.0]: probability of continuing game at game over
# - int((-inf, -1.0]): number of continues at game over before episode to be considered done
settings["continueGame"] = -1.0

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
envId = "TestEnv"

env = diambraArena.make(envId, settings)

observation = env.reset()
showGymObs(observation, env.charNames, env.partnerNames)

while True:

    actions = env.action_space.sample()

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
