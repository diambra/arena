import diambraArena
from diambraArena.gymUtils import showWrapObs
from diambraArena.utils.diambraGamepad import diambraGamepad
import argparse, os
from os.path import expanduser

parser = argparse.ArgumentParser()
parser.add_argument('--romsPath', type=str, required=False, help='Absolute path to roms')
opt = parser.parse_args()
print(opt)

# Mandatory settings
settings = {}
if opt.romsPath is not None:
    settings["romsPath"] = opt.romsPath

# Additional settings
settings["player"] = "Random"
settings["stepRatio"] = 1

# Action space choice
settings["actionSpace"] = "multiDiscrete"
settings["attackButCombination"] = True
settings["envId"] = "HumanExperienceRecorderEnv"

# Gym wrappers settings
wrappersSettings = {}
wrappersSettings["hwcObsResize"] = [128, 128, 1]
wrappersSettings["rewardNormalizationFactor"] = 0.5
wrappersSettings["frameStack"] = 4
wrappersSettings["actionsStack"] = 12
wrappersSettings["scale"] = True

# Gym trajectory recording wrapper kwargs
trajRecSettings = {}
homeDir = expanduser("~")

# Username
trajRecSettings["userName"] = "Alex"

# Path where to save recorderd trajectories
trajRecSettings["filePath"] = os.path.join(homeDir, "diambraArena/trajRecordings",
                                         settings["gameId"])

# If to ignore P2 trajectory (useful when collecting
# only human trajectories while playing as a human against a RL agent)
trajRecSettings["ignoreP2"] = 0

env = diambraArena.make("doapp", settings, wrappersSettings, trajRecSettings)

# GamePad(s) initialization
gamepad = diambraGamepad(env.actionList)
gamepad.start()

observation = env.reset()
showWrapObs(observation, env.nActionsStack, env.charNames, 1, False)

while True:

    actions = gamepad.getActions()

    observation, reward, done, info = env.step(actions)
    showWrapObs(observation, env.nActionsStack, env.charNames, 1, False)
    print("Reward: {}".format(reward))
    print("Done: {}".format(done))
    print("Info: {}".format(info))

    if done:
        observation = env.reset()
        showWrapObs(observation, env.nActionsStack, env.charNames, 1, False)
        break

env.close()
