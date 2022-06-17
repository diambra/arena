#!/usr/bin/env python3
import diambraArena
from diambraArena.gymUtils import show_gym_obs

# Settings
settings = {}

# Player side selection: P1 (left), P2 (right), Random (50% P1, 50% P2)
settings["player"] = "P2"

# Number of steps performed by the game
# for every environment step, bounds: [1, 6]
settings["stepRatio"] = 6

# Native frame resize operation
settings["frameShape"] = [128, 128, 0]  # RBG with 128x128 size
# settings["frameShape"] = [0, 0, 1] # Grayscale with original size
# settings["frameShape"] = [0, 0, 0] # Deactivated (Original size RBG)

# Game continue logic (0.0 by default):
# - [0.0, 1.0]: probability of continuing game at game over
# - int((-inf, -1.0]): number of continues at game over
#                      before episode to be considered done
settings["continueGame"] = 0.0

# If to show game final when game is completed
settings["showFinal"] = False

# Game-specific options (see documentation for details)
# Game difficulty level
settings["difficulty"] = 3

# Character to be used, automatically extended with "Random" for games
# requiring to select more than one character (e.g. Tekken Tag Tournament)
settings["characters"] = [["Random"], ["Random"]]

# Character outfit
settings["charOutfits"] = [2, 2]

# If to use discrete or multiDiscrete action space
settings["actionSpace"] = "discrete"

# If to use attack buttons combinations actions
settings["attackButCombination"] = True

env = diambraArena.make("doapp", settings)

observation = env.reset()
show_gym_obs(observation, env.charNames)

while True:

    actions = env.action_space.sample()

    observation, reward, done, info = env.step(actions)
    show_gym_obs(observation, env.charNames)
    print("Reward: {}".format(reward))
    print("Done: {}".format(done))
    print("Info: {}".format(info))

    if done:
        observation = env.reset()
        show_gym_obs(observation, env.charNames)
        break

env.close()
