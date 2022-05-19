import diambraArena
from diambraArena.gymUtils import showWrapObs
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--romsPath', type=str, required=False, help='Absolute path to roms')
opt = parser.parse_args()
print(opt)

# Mandatory settings
settings = {}
if opt.romsPath is not None:
    settings["romsPath"] = opt.romsPath

# Gym wrappers settings
wrappersSettings = {}

# Number of no-Op actions to be executed at the beginning of the episode (0 by default)
wrappersSettings["noOpMax"] = 0

# Number of steps for which the same action should be sent (1 by default)
wrappersSettings["stickyActions"] = 1

# Frame resize operation spec (deactivated by default)
wrappersSettings["hwcObsResize"] = [128, 128, 1]

# Coefficient to be used for reward normalization
# It is activated if different from 1.0,
# The normalization is performed by dividing the reward value
# by the product of this coefficient times the value of the full health bar
# reward = reward / (C * fullHealthBarValue)
wrappersSettings["rewardNormalizationFactor"] = 0.5

# If to clip rewards (False by default)
wrappersSettings["clipRewards"] = False

# Number of frames to be stacked together (1 by default)
wrappersSettings["frameStack"] = 4

# Frames interval when stacking (1 by default)
wrappersSettings["dilation"] = 1

# How many past actions to stack together (1 by default)
wrappersSettings["actionsStack"] = 12

# If to scale observation numerical values (deactivated by default)
wrappersSettings["scale"] = True

# Scaling interval (0 = [0.0, 1.0], 1 = [-1.0, 1.0])
wrappersSettings["scaleMod"] = 0

env = diambraArena.make("doapp", settings, wrappersSettings)

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
