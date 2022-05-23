#!/usr/bin/env python3
import diambraArena
import os
import multiprocessing

def envExec(envAddress):

    # Settings
    settings = {"envAddress": envAddress}

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

if __name__ == '__main__':

    envs = os.getenv("DIAMBRA_ENVS", "").split()
    print("Using the following environment addresses:")
    for address in envs:
        print(" - {}".format(address))

    p = multiprocessing.Pool(multiprocessing.cpu_count())
    p.map(envExec, envs)

