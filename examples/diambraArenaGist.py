#!/usr/bin/env python3
import diambraArena
import argparse
import os

envs = os.getenv("DIAMBRA_ENVS", "").split()
if len(envs) >= 1:
    defaultEnvAddress = envs[0]

parser = argparse.ArgumentParser()
parser.add_argument('--envAddress', type=str, default=defaultEnvAddress, help='diambraEngine Address')

opt = parser.parse_args()
print(opt)

# Settings
settings = {
    "envAddress": opt.envAddress,
}

env = diambraArena.make("doapp", settings)

observation = env.reset()

while True:
    env.render()

    actions = env.action_space.sample()

    observation, reward, done, info = env.step(actions)

    if done:
        observation = env.reset()
        break

env.close()
