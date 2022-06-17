import diambraArena
from diambraArena.utils.diambraGamepad import DiambraGamepad
import prova
import os
from os.path import expanduser

prova.ciao()

# Environment Settings
settings = {}
settings["player"] = "Random"
settings["stepRatio"] = 1
settings["frameShape"] = [128, 128, 1]
settings["actionSpace"] = "multiDiscrete"
settings["attackButCombination"] = True

# Gym wrappers settings
wrappers_settings = {}
wrappers_settings["rewardNormalization"] = True
wrappers_settings["frameStack"] = 4
wrappers_settings["actionsStack"] = 12
wrappers_settings["scale"] = True

# Gym trajectory recording wrapper kwargs
traj_rec_settings = {}
home_dir = expanduser("~")

# Username
traj_rec_settings["userName"] = "Alex"

# Path where to save recorderd trajectories
game_id = "doapp"
traj_rec_settings["filePath"] = os.path.join(
    home_dir, "diambraArena/trajRecordings", game_id)

# If to ignore P2 trajectory (useful when collecting
# only human trajectories while playing as a human against a RL agent)
traj_rec_settings["ignoreP2"] = 0

env = diambraArena.make(game_id, settings,
                        wrappers_settings, traj_rec_settings)

# GamePad(s) initialization
gamepad = DiambraGamepad(env.actionList)
gamepad.start()

observation = env.reset()

while True:

    env.render()

    actions = gamepad.get_actions()

    observation, reward, done, info = env.step(actions)

    if done:
        observation = env.reset()
        break

gamepad.stop()
env.close()
