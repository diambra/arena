#!/usr/bin/env python3
import diambraArena
from diambraArena.gymUtils import showWrapObs
import argparse
import os
from os import listdir
import numpy as np

try:
    parser = argparse.ArgumentParser()
    parser.add_argument('--path',     type=str, required=True,
                        help='Path where recorded files are stored')
    parser.add_argument('--nProc',    type=int, default=1,
                        help='Number of processors [(1), 2]')
    parser.add_argument('--hardCore', type=int, default=0,
                        help='Hard Core Mode [(0=False), 1=True]')
    parser.add_argument('--viz',      type=int, default=0,
                        help='Visualization [(0=False), 1=True]')
    parser.add_argument('--waitKey',  type=int, default=1,
                        help='CV2 WaitKey [0, 1]')
    opt = parser.parse_args()
    print(opt)

    vizFlag = True if opt.viz == 1 else False

    # Show files in folder
    trajRecFolder = opt.path
    trajectoriesFiles = [os.path.join(trajRecFolder, f) for f in listdir(
        trajRecFolder) if os.path.isfile(os.path.join(trajRecFolder, f))]
    print(trajectoriesFiles)

    diambraILSettings = {}
    diambraILSettings["trajFilesList"] = trajectoriesFiles
    diambraILSettings["totalCpus"] = opt.nProc

    if opt.hardCore == 0:
        env = diambraArena.imitationLearning(**diambraILSettings)
    else:
        env = diambraArena.imitationLearningHardCore(**diambraILSettings)

    observation = env.reset()
    env.render(mode="human")

    env.trajSummary()

    showWrapObs(observation, env.nActionsStack,
                env.charNames, opt.waitKey, vizFlag)

    cumulativeEpRew = 0.0
    cumulativeEpRewAll = []

    maxNumEp = 10
    currNumEp = 0

    while currNumEp < maxNumEp:

        dummyActions = 0
        observation, reward, done, info = env.step(dummyActions)
        env.render(mode="human")

        action = info["action"]

        print("Action:", action)
        print("reward:", reward)
        print("done = ", done)
        for k, v in info.items():
            print("info[\"{}\"] = {}".format(k, v))
        showWrapObs(observation, env.nActionsStack,
                    env.charNames, opt.waitKey, vizFlag)

        print("----------")

        # if done:
        #    observation = info[procIdx]["terminal_observation"]

        cumulativeEpRew += reward

        if (np.any([info["roundDone"], info["stageDone"], info["gameDone"]])
                and not done):
            # Frames equality check
            if opt.hardCore == 0:
                for frameIdx in range(observation["frame"].shape[2]-1):
                    if np.any(observation["frame"][:, :, frameIdx] != observation["frame"][:, :, frameIdx+1]):
                        raise RuntimeError("Frames inside observation after "
                                           "round/stage/game/episode done are "
                                           "not equal. Dones =",
                                           info["roundDone"],
                                           info["stageDone"],
                                           info["gameDone"],
                                           info["epone"])
            else:
                for frameIdx in range(observation.shape[2]-1):
                    if np.any(observation[:, :, frameIdx] != observation[:, :, frameIdx+1]):
                        raise RuntimeError("Frames inside observation after "
                                           "round/stage/game/episode done are "
                                           "not equal. Dones =",
                                           info["roundDone"],
                                           info["stageDone"],
                                           info["gameDone"],
                                           info["epone"])

        if np.any(env.exhausted):
            break

        if done:
            currNumEp += 1
            print("Ep. # = ", currNumEp)
            print("Ep. Cumulative Rew # = ", cumulativeEpRew)

            cumulativeEpRewAll.append(cumulativeEpRew)
            cumulativeEpRew = 0.0

            observation = env.reset()
            env.render(mode="human")
            showWrapObs(observation, env.nActionsStack,
                        env.charNames, opt.waitKey, vizFlag)

    if diambraILSettings["totalCpus"] == 1:
        print("All ep. rewards =", cumulativeEpRewAll)
        print("Mean cumulative reward =", np.mean(cumulativeEpRewAll))
        print("Std cumulative reward =", np.std(cumulativeEpRewAll))

    env.close()

    print("ALL GOOD!")
except Exception as e:
    print(e)
    print("ALL BAD")
