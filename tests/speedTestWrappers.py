#!/usr/bin/env python3
import diambraArena
import argparse, time, os
import numpy as np

def reject_outliers(data):
    m = 2
    u = np.mean(data)
    s = np.std(data)
    filtered = [e for e in data if (u - 2 * s < e < u + 2 * s)]
    return filtered

if __name__ == '__main__':

    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--gameId',      type=str, default="doapp",    help='Game ID [(doapp), sfiii3n, tektagt, umk3]')
        parser.add_argument('--player',      type=str, default="Random",   help='Player [(Random), P1, P2, P1P2]')
        parser.add_argument('--actionSpace', type=str, default="discrete", help='(discrete)/multidiscrete')
        parser.add_argument('--attButComb',  type=int, default=0,          help='If to use attack button combinations (0=False)/1=True')
        parser.add_argument('--targetSpeed', type=int, default=100,        help='Reference speed')
        opt = parser.parse_args()
        print(opt)

        # Settings
        settings = {}
        settings["player"]         = opt.player
        settings["stepRatio"]      = 1

        settings["actionSpace"] = opt.actionSpace
        settings["attackButCombination"] = opt.attButComb

        # Recording settings
        trajRecSettings = None

        # Env wrappers settings
        wrappersSettings = {}
        wrappersSettings["noOpMax"] = 0
        wrappersSettings["stickyActions"] = 1
        wrappersSettings["hwcObsResize"] = [128, 128, 1]
        wrappersSettings["rewardNormalization"] = True
        wrappersSettings["clipRewards"] = False
        wrappersSettings["frameStack"] = 4
        wrappersSettings["dilation"] = 1
        wrappersSettings["actionsStack"] = 12
        wrappersSettings["scale"] = True
        wrappersSettings["scaleMod"] = 0

        env = diambraArena.make(opt.gameId, settings, wrappersSettings, trajRecSettings)

        observation = env.reset()
        nStep = 0

        fpsVal = []

        while nStep < 1000:

            nStep+=1
            actions = [None, None]
            if settings["player"] != "P1P2":
                actions = env.action_space.sample()
            else:
                for idx in range(2):
                    actions[idx] = env.action_space["P{}".format(idx+1)].sample()

            if settings["player"] == "P1P2" or settings["actionSpace"] != "discrete":
                actions = np.append(actions[0], actions[1])

            tic = time.time()
            observation, reward, done, info = env.step(actions)
            toc = time.time()
            fps = 1/(toc-tic)
            fpsVal.append(fps)

            if done:
                observation = env.reset()
                break

        env.close()

        fpsVal2 = reject_outliers(fpsVal)
        avgFps = np.mean(fpsVal2)
        print("Average speed = {} FPS, STD {} FPS".format(avgFps, np.std(fpsVal2)))

        if abs(avgFps - opt.targetSpeed) > opt.targetSpeed*0.025:
            raise RuntimeError("Fps different than expected: {} VS {}".format(avgFps, opt.targetSpeed))

        print("ALL GOOD!")
    except Exception as e:
        print(e)
        print("ALL BAD")
