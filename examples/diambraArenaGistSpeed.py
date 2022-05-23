#!/usr/bin/env python3
import diambraArena
import argparse
import os, time

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

while nStep < 1000:

    nStep+=1
    actions = env.action_space.sample()

    tic = time.time()
    observation, reward, done, info = env.step(actions)
    toc = time.time()
    print(1/(toc-tic))
    tic = toc

    if done:
        observation = env.reset()
        break
toc = time.time()
print("Delta T = ", toc-tic)
print("Nsteps = ", nStep)
print("FPS = ", nStep/(toc-tic))

env.close()
