import diambraArena
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--romsPath', type=str, required=False, help='Absolute path to roms')
opt = parser.parse_args()
print(opt)

# Mandatory parameters
settings = {}
settings["gameId"]      = "doapp" # Game selection
settings["actionSpace"] = "discrete" # Game selection
if opt.romsPath is not None:
    settings["romsPath"] = opt.romsPath # Path to roms folder
envId = "TestEnv" # This ID must be unique for every instance of the environment

env = diambraArena.make(envId, settings)

env.printActions()

observation = env.reset()

while True:

    actions = env.action_space.sample()

    observation, reward, done, info = env.step(actions)

    if done:
        observation = env.reset()
        break

env.close()
