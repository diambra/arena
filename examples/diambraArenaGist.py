import diambraArena
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--romsPath', type=str, required=False, help='Absolute path to roms')
opt = parser.parse_args()
print(opt)

# Settings
settings = {}
# Game Selection
settings["gameId"] = "doapp"

if opt.romsPath is not None:
    # Path to roms folder
    settings["romsPath"] = opt.romsPath

env = diambraArena.make(settings)

observation = env.reset()

while True:

    actions = env.action_space.sample()

    observation, reward, done, info = env.step(actions)

    if done:
        observation = env.reset()
        break

env.close()
