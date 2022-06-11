import diambraArena
from diambraArena.utils.diambraGamepad import diambraGamepad
import argparse, os
from os.path import expanduser

# Environment Settings
settings = {}
settings["player"] = "Random"
settings["stepRatio"] = 1
settings["frameShape"] = [128, 128, 1]
settings["actionSpace"] = "multiDiscrete"
settings["attackButCombination"] = True

# Gym wrappers settings
wrappersSettings = {}
wrappersSettings["rewardNormalization"] = True
wrappersSettings["frameStack"] = 4
wrappersSettings["actionsStack"] = 12
wrappersSettings["scale"] = True

# Gym trajectory recording wrapper kwargs
trajRecSettings = {}
homeDir = expanduser("~")

# Username
trajRecSettings["userName"] = "Alex"

# Path where to save recorderd trajectories
gameId = "doapp"
trajRecSettings["filePath"] = os.path.join(homeDir, "diambraArena/trajRecordings", gameId)

# If to ignore P2 trajectory (useful when collecting
# only human trajectories while playing as a human against a RL agent)
trajRecSettings["ignoreP2"] = 0

env = diambraArena.make(gameId, settings, wrappersSettings, trajRecSettings)

# GamePad(s) initialization
gamepad = diambraGamepad(env.actionList)
gamepad.start()

observation = env.reset()

while True:

    env.render()

    actions = gamepad.getActions()

    observation, reward, done, info = env.step(actions)

    if done:
        observation = env.reset()
        break

gamepad.stop()
env.close()
