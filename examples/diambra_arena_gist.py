#!/usr/bin/env python3
import diambra.arena

if __name__ == '__main__':

    env = diambra.arena.make("doapp")
    observation = env.reset()

    while True:
        env.render()

        actions = env.action_space.sample()

        observation, reward, done, info = env.step(actions)

        if done:
            observation = env.reset()
            break

    env.close()
