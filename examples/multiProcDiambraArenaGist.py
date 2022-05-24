#!/usr/bin/env python3
import diambraArena
import os
import multiprocessing

def envExec(rank):
    env = diambraArena.makeAll("doapp")[rank]

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
    p = multiprocessing.Pool(multiprocessing.cpu_count())
    p.map(envExec, range(len(diambraArena.makeAll("doapp"))))