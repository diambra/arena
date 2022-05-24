#!/usr/bin/env python3
import diambraArena
import os, time
import numpy as np

def reject_outliers(data):
    m = 2
    u = np.mean(data)
    s = np.std(data)
    filtered = [e for e in data if (u - 2 * s < e < u + 2 * s)]
    return filtered

# Settings
settings = {"stepRatio": 1}

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
