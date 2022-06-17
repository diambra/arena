#!/usr/bin/env python3
import diambraArena
import argparse
import time
import numpy as np


def reject_outliers(data):
    u = np.mean(data)
    s = np.std(data)
    filtered = [e for e in data if (u - 2 * s < e < u + 2 * s)]
    return filtered


if __name__ == '__main__':

    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--gameId', type=str, default="doapp",
                            help='Game ID [(doapp), sfiii3n, tektagt, umk3]')
        parser.add_argument('--player', type=str, default="Random",
                            help='Player [(Random), P1, P2, P1P2]')
        parser.add_argument('--actionSpace', type=str,
                            default="discrete", help='(discrete)/multidis.')
        parser.add_argument('--attButComb',  type=int, default=0,
                            help='Use attack button combinations (0=F)/1=T')
        parser.add_argument('--targetSpeed', type=int,
                            default=100,        help='Reference speed')
        opt = parser.parse_args()
        print(opt)

        # Settings
        settings = {}
        settings["player"] = opt.player
        settings["stepRatio"] = 1
        settings["frameShape"] = [128, 128, 1]

        settings["actionSpace"] = opt.actionSpace
        settings["attackButCombination"] = opt.attButComb

        # Recording settings
        traj_rec_settings = None

        # Env wrappers settings
        wrappers_settings = {}
        wrappers_settings["noOpMax"] = 0
        wrappers_settings["stickyActions"] = 1
        wrappers_settings["rewardNormalization"] = True
        wrappers_settings["clipRewards"] = False
        wrappers_settings["frameStack"] = 4
        wrappers_settings["dilation"] = 1
        wrappers_settings["actionsStack"] = 12
        wrappers_settings["scale"] = True
        wrappers_settings["scaleMod"] = 0

        env = diambraArena.make(opt.gameId, settings,
                                wrappers_settings, traj_rec_settings)

        observation = env.reset()
        n_step = 0

        fps_val = []

        while n_step < 1000:

            n_step += 1
            actions = [None, None]
            if settings["player"] != "P1P2":
                actions = env.action_space.sample()
            else:
                for idx in range(2):
                    actions[idx] = env.action_space["P{}".format(
                        idx+1)].sample()

            if (settings["player"] == "P1P2"
                    or settings["actionSpace"] != "discrete"):
                actions = np.append(actions[0], actions[1])

            tic = time.time()
            observation, reward, done, info = env.step(actions)
            toc = time.time()
            fps = 1/(toc-tic)
            fps_val.append(fps)

            if done:
                observation = env.reset()
                break

        env.close()

        fps_val2 = reject_outliers(fps_val)
        avg_fps = np.mean(fps_val2)
        print("Average speed = "
              "{} FPS, STD {} FPS".format(avg_fps, np.std(fps_val2)))

        if abs(avg_fps - opt.targetSpeed) > opt.targetSpeed*0.025:
            raise RuntimeError(
                "Fps different than expected: "
                "{} VS {}".format(avg_fps, opt.targetSpeed))

        print("ALL GOOD!")
    except Exception as e:
        print(e)
        print("ALL BAD")
