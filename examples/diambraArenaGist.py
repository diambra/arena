#!/usr/bin/env python3
import diambraArena
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument('--pipesPath', type=str, default=os.getenv('PIPES_PATH', ''), help='Path to diambraApp pipes')
parser.add_argument('--envId', type=str, default='0', help='envID')

opt = parser.parse_args()
print(opt)

# Settings
settings = {
    "pipesPath": opt.pipesPath,
    "envId": opt.envId,
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
