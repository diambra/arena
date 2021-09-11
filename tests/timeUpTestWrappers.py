import diambraArena
from diambraArena.gymUtils import envSpacesSummary, discreteToMultiDiscreteAction, showWrapObs
import argparse, time, os
from os.path import expanduser
import numpy as np

if __name__ == '__main__':
    timeDepSeed = int((time.time()-int(time.time()-0.5))*1000)

    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--romsPath',       type=str,   required=True,   help='Absolute path to roms')
        parser.add_argument('--gameId',         type=str,   default="doapp", help='Game ID')
        parser.add_argument('--continueGame',   type=float, default=0.0,     help='ContinueGame flag (-inf,+1.0]')
        parser.add_argument('--firstRoundAct',  type=int,   default=0,       help='Actions active for first round (0=False)')
        parser.add_argument('--interactiveViz', type=int,   default=0,       help='Interactive Visualization (0=False)')
        parser.add_argument('--libPath',        type=str,   default="",      help='Path to diambraEnvLib')
        opt = parser.parse_args()
        print(opt)

        vizFlag = bool(opt.interactiveViz)
        waitKey = 1;
        if vizFlag:
            waitKey = 0

        homeDir = expanduser("~")

        # Common settings
        diambraKwargs = {}
        diambraKwargs["romsPath"] = opt.romsPath
        if opt.libPath != "":
            diambraKwargs["libPath"]  = opt.libPath

        diambraKwargs["gameId"]     = opt.gameId
        diambraKwargs["player"]     = "P1P2"
        diambraKwargs["characters"] = [["Random", "Random"], ["Random", "Random"]]

        diambraKwargs["stepRatio"] = 3
        diambraKwargs["render"] = True
        diambraKwargs["lockFps"] = False

        diambraKwargs["continueGame"] = opt.continueGame
        diambraKwargs["showFinal"]    = False

        diambraKwargs["charOutfits"] = [2, 2]

        # DIAMBRA gym kwargs
        diambraGymKwargs = {}
        diambraGymKwargs["actionSpace"] = ["discrete", "discrete"]
        diambraGymKwargs["attackButCombinations"] = [False, False]

        trajRecKwargs = None

        # Env wrappers kwargs
        wrapperKwargs = {}
        wrapperKwargs["noOpMax"] = 0
        wrapperKwargs["hwcObsResize"] = [128, 128, 1]
        wrapperKwargs["normalizeRewards"] = True
        wrapperKwargs["clipRewards"] = False
        wrapperKwargs["frameStack"] = 4
        wrapperKwargs["dilation"] = 1
        wrapperKwargs["actionsStack"] = 12
        wrapperKwargs["scale"] = True
        wrapperKwargs["scaleMod"] = 0

        envId = opt.gameId + "_timeUpTestWrappers"
        hardCore = False
        env = diambraArena.make(envId, diambraKwargs, diambraGymKwargs,
                                wrapperKwargs, trajRecKwargs,
                                seed=timeDepSeed, hardCore=hardCore)

        # Print environment obs and action spaces summary
        envSpacesSummary(env)

        actionsPrintDict = env.printActionsDict

        observation = env.reset()

        while True:

            actions = [None, None]
            for idx in range(2):
                if opt.firstRoundAct == 1:
                    actions[idx] = env.action_space["P{}".format(idx+1)].sample()
                else:
                    actions[idx] = 0

            actions = np.append(actions[0], actions[1])

            observation, reward, done, info = env.step(actions)

            print("action =", actions)
            print("reward =", reward)
            print("done =", done)
            for k, v in info.items():
                print("info[\"{}\"] = {}".format(k, v))
            showWrapObs(observation, wrapperKwargs["actionsStack"], env.charNames, waitKey, vizFlag)
            print("----------")

            if done:
                print("Resetting Env")
                observation = env.reset()
                showWrapObs(observation, wrapperKwargs["actionsStack"], env.charNames, waitKey, vizFlag)
                break

        env.close()

        print("ALL GOOD!")
    except Exception as e:
        print(e)
        print("ALL BAD")
