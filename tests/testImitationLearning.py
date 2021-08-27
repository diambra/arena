import sys, os, time, cv2
from os.path import expanduser
from os import listdir
import numpy as np
import argparse

import diambraArena

def showObs(observation, waitKey=1, viz=True):
    if type(observation) == dict:
        for k, v in observation.items():
            if k != "frame":
                if type(v) == dict:
                    for k2, v2 in v.items():
                        if type(v2) == dict:
                            for k3, v3 in v2.items():
                                print("observation[\"{}\"][\"{}\"][\"{}\"]:\n{}"\
                                      .format(k,k2,k3,np.reshape(v3, [actionsStack,-1])))
                        else:
                            print("observation[\"{}\"][\"{}\"]: {}".format(k,k2,v2))
                else:
                    print("observation[\"{}\"]: {}".format(k,v))
            else:
                print("observation[\"frame\"].shape:", observation["frame"].shape)

        if viz:
            obs = np.array(observation["frame"]).astype(np.float32)
    else:
        if viz:
            obs = np.array(observation).astype(np.float32)

    if viz:
        for idx in range(obs.shape[2]):
            cv2.imshow("image"+str(idx), obs[:,:,idx])

        cv2.waitKey(waitKey)

try:
    parser = argparse.ArgumentParser()
    parser.add_argument('--path',     type=str, required=True, help='Path where recorded files are stored')
    parser.add_argument('--nProc',    type=int, default=1,     help='Number of processors [(1), 2]')
    parser.add_argument('--hardCore', type=int, default=0,     help='Hard Core Mode [(0=False), 1=True]')
    parser.add_argument('--viz',      type=int, default=0,     help='Visualization [(0=False), 1=True]')
    parser.add_argument('--waitKey',  type=int, default=1,     help='CV2 WaitKey [0, 1]')
    opt = parser.parse_args()
    print(opt)

    homeDir = expanduser("~")

    vizFlag = True if opt.viz == 1 else False

    # Show files in folder
    trajRecFolder = opt.path
    trajectoriesFiles = [os.path.join(trajRecFolder, f) for f in listdir(trajRecFolder) if os.path.isfile(os.path.join(trajRecFolder, f))]
    print(trajectoriesFiles)

    diambraILKwargs = {}
    diambraILKwargs["trajFilesList"] = trajectoriesFiles
    diambraILKwargs["totalCpus"] = opt.nProc

    if opt.hardCore == 0:
        env = diambraImitationLearning(**diambraILKwargs)
    else:
        env = diambraImitationLearningHardCore(**diambraILKwargs)

    observation = env.reset()
    env.render(mode="human")

    nChars = env.nChars
    charNames = env.charNames
    nActions = env.nActions
    actionsStack = env.actionsStack

    env.trajSummary()

    showObs(observation, opt.waitKey, vizFlag)

    cumulativeEpRew = 0.0
    cumulativeEpRewAll = []

    maxNumEp = 10
    currNumEp = 0

    while currNumEp < maxNumEp:

        dummyActions = 0
        observation, reward, done, info = env.step(dummyActions)

        if np.any(env.exhausted):
            break

        env.render(mode="human")

        observation = observation
        reward = reward
        done = done
        action = info["action"]

        print("Action:", action)
        print("reward:", reward)
        print("done = ", done)
        for k, v in info.items():
            print("info[\"{}\"] = {}".format(k, v))
        showObs(observation, opt.waitKey, vizFlag)

        print("----------")

        #if done:
        #    observation = info[procIdx]["terminal_observation"]

        cumulativeEpRew += reward

        if np.any([info["roundDone"], info["stageDone"], info["gameDone"]]) and not done:
            # Frames equality check
            if opt.hardCore == 0:
                for frameIdx in range(observation["frame"].shape[2]-1):
                    if np.any(observation["frame"][:,:,frameIdx] != observation["frame"][:,:,frameIdx+1]):
                        raise RuntimeError("Frames inside observation after round/stage/game/episode done are not equal. Dones =", info["roundDone"], info["stageDone"], info["gameDone"], info["epone"])
            else:
                for frameIdx in range(observation.shape[2]-1):
                    if np.any(observation[:,:,frameIdx] != observation[:,:,frameIdx+1]):
                        raise RuntimeError("Frames inside observation after round/stage/game/episode done are not equal. Dones =", info["roundDone"], info["stageDone"], info["gameDone"], info["epone"])


        if done:
            currNumEp += 1
            print("Ep. # = ", currNumEp)
            print("Ep. Cumulative Rew # = ", cumulativeEpRew)

            cumulativeEpRewAll.append(cumulativeEpRew)
            cumulativeEpRew = 0.0

            observation = env.reset()
            showObs(observation, opt.waitKey, vizFlag)

    if diambraILKwargs["totalCpus"] == 1:
        print("All ep. rewards =", cumulativeEpRewAll)
        print("Mean cumulative reward =", np.mean(cumulativeEpRewAll))
        print("Std cumulative reward =", np.std(cumulativeEpRewAll))

    print("ALL GOOD!")
except Exception as e:
    print(e)
    print("ALL BAD")
