#!/usr/bin/env python3
# WORKING
from diambra.arena.make_env import make
env = make("doapp")

# NOT WORKING
# from diambra import arena
# env = arena.make_env.make("doapp")

# NOT WORKING (after modifying __init.py__ in diambra/arena/ folder)
# from diambra import arena
# env = arena.make("doapp")

observation = env.reset()

while True:
    env.render()

    actions = env.action_space.sample()

    observation, reward, done, info = env.step(actions)

    if done:
        observation = env.reset()
        break

env.close()
