#!/usr/bin/env python3
import diambraArena
import argparse
import os, time
import numpy as np

def reject_outliers(data):
    m = 2
    u = np.mean(data)
    s = np.std(data)
    filtered = [e for e in data if (u - 2 * s < e < u + 2 * s)]
    return filtered

defaultEnvAddress = "localhost:50051"
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
    "stepRatio": 6,
    "render": False,
    "lockFps": False,
    "stepRatio":1
}

env = diambraArena.make("sfiii3n", settings)

observation = env.reset()
nStep = 0

fpsVal = []

while nStep < 1000:

    nStep+=1
    actions = env.action_space.sample()

    tic = time.time()
    observation, reward, done, info = env.step(actions)
    toc = time.time()
    fps = 1/(toc-tic)
    tic = toc
    fpsVal.append(fps)

    if done:
        observation = env.reset()
        break

fpsVal2 = reject_outliers(fpsVal)
avgFps = np.mean(fpsVal2)
print("avg FPS = ", avgFps)

env.close()
