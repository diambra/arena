#!/usr/bin/env python3
import diambraArena
import os

env = diambraArena.make("doapp")

observation = env.reset()

while True:
    env.render()

    actions = env.action_space.sample()

    observation, reward, done, info = env.step(actions)

    if done:
        observation = env.reset()
        break

env.close()
