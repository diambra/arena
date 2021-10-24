import diambraArena
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--romsPath', type=str, required=False, help='Absolute path to roms')
opt = parser.parse_args()
print(opt)

# Mandatory settings
settings = {}
settings["gameId"]      = "doapp" # Game selection
if opt.romsPath is not None:
    settings["romsPath"] = opt.romsPath # Path to roms folder

env = diambraArena.make("TestEnv", settings)

observation = env.reset()

while True:

    actions = env.action_space.sample()

    observation, reward, done, info = env.step(actions)

    if done:
        observation = env.reset()
        break

env.close()
