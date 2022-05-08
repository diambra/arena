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

        # Settings
        settings = {}
        settings["romsPath"] = opt.romsPath
        if opt.libPath != "":
            settings["libPath"]  = opt.libPath

        settings["player"]     = "P1P2"

        settings["stepRatio"] = 3
        settings["render"] = True
        settings["lockFps"] = False

        settings["continueGame"] = opt.continueGame
        settings["showFinal"]    = False

        settings["actionSpace"] = ["discrete", "discrete"]
        settings["attackButCombination"] = [False, False]

        settings["hardCore"] = False

        trajRecSettings = None

        # Env wrappers settings
        wrappersSettings = {}
        wrappersSettings["noOpMax"] = 0
        wrappersSettings["stickyActions"] = 1
        wrappersSettings["hwcObsResize"] = [128, 128, 1]
        wrappersSettings["normalizeRewards"] = True
        wrappersSettings["clipRewards"] = False
        wrappersSettings["frameStack"] = 4
        wrappersSettings["dilation"] = 1
        wrappersSettings["actionsStack"] = 12
        wrappersSettings["scale"] = True
        wrappersSettings["scaleMod"] = 0

        settings["envId"] = opt.gameId + "_timeUpTestWrappers"
        env = diambraArena.make(opt.gameId, settings, wrappersSettings, trajRecSettings,
                                seed=timeDepSeed)

        # Print environment obs and action spaces summary
        envSpacesSummary(env)

        observation = env.reset()

        while True:

            actions = [None, None]
            for idx in range(2):
                if opt.firstRoundAct == 1 and observation["P1"]["ownWins"] == 0.0 and observation["P1"]["oppWins"] == 0.0:
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
            showWrapObs(observation, wrappersSettings["actionsStack"], env.charNames, env.partnerNames, waitKey, vizFlag)
            print("----------")

            if done:
                print("Resetting Env")
                observation = env.reset()
                showWrapObs(observation, wrappersSettings["actionsStack"], env.charNames, env.partnerNames, waitKey, vizFlag)
                break

        env.close()

        print("ALL GOOD!")
    except Exception as e:
        print(e)
        print("ALL BAD")
