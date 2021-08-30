import sys, os, time
import numpy as np
import argparse

import diambraArena
from diambraArena.gymUtils import envSpacesSummary, discreteToMultiDiscreteAction, showGymObs

if __name__ == '__main__':
    timeDepSeed = int((time.time()-int(time.time()-0.5))*1000)

    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--romsPath',       type=str,   required=True,      help='Absolute path to roms')
        parser.add_argument('--gameId',         type=str,   default="doapp",    help='Game ID [(doapp), sfiii3n, tektagt, umk3]')
        parser.add_argument('--player',         type=str,   default="Random",   help='Player [(Random), P1, P2, P1P2]')
        parser.add_argument('--character1',     type=str,   default="Random",   help='Character P1 (Random)')
        parser.add_argument('--character2',     type=str,   default="Random",   help='Character P2 (Random)')
        parser.add_argument('--character1_2',   type=str,   default="Random",   help='Character P1_2 (Random)')
        parser.add_argument('--character2_2',   type=str,   default="Random",   help='Character P2_2 (Random)')
        parser.add_argument('--frameRatio',     type=int,   default=3,          help='Frame ratio')
        parser.add_argument('--nEpisodes',      type=int,   default=1,          help='Number of episodes')
        parser.add_argument('--continueGame',   type=float, default=-1.0,       help='ContinueGame flag (-inf,+1.0]')
        parser.add_argument('--actionSpace',    type=str,   default="discrete", help='(discrete)/multiDiscrete')
        parser.add_argument('--attButComb',     type=int,   default=0,          help='If to use attack button combinations (0=False)/1=True')
        parser.add_argument('--noAction',       type=int,   default=0,          help='If to use no action policy (0=False)')
        parser.add_argument('--hardCore',       type=int,   default=0,          help='Hard core mode (0=False)')
        parser.add_argument('--interactiveViz', type=int,   default=0,          help='Interactive Visualization (0=False)')
        parser.add_argument('--libPath',        type=str,   default="",         help='Path to diambraEnvLib')
        opt = parser.parse_args()
        print(opt)

        vizFlag = bool(opt.interactiveViz)
        waitKey = 1;
        if vizFlag:
            waitKey = 0

        # Common settings
        diambraKwargs = {}
        diambraKwargs["romsPath"] = opt.romsPath
        if opt.libPath != "":
            diambraKwargs["libPath"]  = opt.libPath

        diambraKwargs["gameId"]     = opt.gameId
        diambraKwargs["player"]     = opt.player
        diambraKwargs["characters"] = [[opt.character1, opt.character1_2], [opt.character2, opt.character2_2]]

        diambraKwargs["mameDiambraStepRatio"] = opt.frameRatio
        diambraKwargs["render"] = True
        diambraKwargs["lockFps"] = False

        diambraKwargs["continueGame"] = opt.continueGame
        diambraKwargs["showFinal"]    = False

        diambraKwargs["charOutfits"] = [2, 2]

        # DIAMBRA gym kwargs
        diambraGymKwargs = {}
        diambraGymKwargs["actionSpace"] = [opt.actionSpace, opt.actionSpace]
        diambraGymKwargs["attackButCombinations"] = [opt.attButComb, opt.attButComb]
        if diambraKwargs["player"] != "P1P2":
            diambraGymKwargs["actionSpace"] = diambraGymKwargs["actionSpace"][0]
            diambraGymKwargs["attackButCombinations"] = diambraGymKwargs["attackButCombinations"][0]

        envId = opt.gameId + "_randomTestGym"
        hardCore = False if opt.hardCore == 0 else True
        env = diambraArena.make(envId, diambraKwargs, diambraGymKwargs,
                                wrapperKwargs={"normalizeRewards": False},
                                seed=timeDepSeed, hardCore=hardCore)

        # Print environment obs and action spaces summary
        envSpacesSummary(env)

        actionsPrintDict = env.printActionsDict

        observation = env.reset()

        cumulativeEpRew = 0.0
        cumulativeEpRewAll = []

        maxNumEp = opt.nEpisodes
        currNumEp = 0

        while currNumEp < maxNumEp:

            actions = [None, None]
            if diambraKwargs["player"] != "P1P2":
                actions = env.action_space.sample()

                if opt.noAction == 1:
                    if diambraGymKwargs["actionSpace"] == "multiDiscrete":
                        for iEl, _ in enumerate(actions):
                            actions[iEl] = 0
                    else:
                        actions = 0

                if diambraGymKwargs["actionSpace"] == "discrete":
                    moveAction, attAction = discreteToMultiDiscreteAction(actions, env.nActions[0][0])
                else:
                    moveAction, attAction = actions[0], actions[1]

                print("(P1) {} {}".format(actionsPrintDict[0][moveAction],
                                          actionsPrintDict[1][attAction]))

            else:
                for idx in range(2):
                    actions[idx] = env.action_space["P{}".format(idx+1)].sample()

                    if opt.noAction == 1 and idx == 0:
                        if diambraGymKwargs["actionSpace"][idx] == "multiDiscrete":
                            for iEl, _ in enumerate(actions[idx]):
                                actions[idx][iEl] = 0
                        else:
                            actions[idx] = 0

                    if diambraGymKwargs["actionSpace"][idx] == "discrete":
                        moveAction, attAction = discreteToMultiDiscreteAction(actions[idx], env.nActions[idx][0])
                    else:
                        moveAction, attAction = actions[idx][0], actions[idx][1]

                    print("(P{}) {} {}".format(idx+1, actionsPrintDict[0][moveAction],
                                                      actionsPrintDict[1][attAction]))

            if diambraKwargs["player"] == "P1P2" or diambraGymKwargs["actionSpace"] != "discrete":
                actions = np.append(actions[0], actions[1])

            observation, reward, done, info = env.step(actions)

            cumulativeEpRew += reward
            print("action =", actions)
            print("reward =", reward)
            print("done =", done)
            for k, v in info.items():
                print("info[\"{}\"] = {}".format(k, v))
            showGymObs(observation, waitKey, vizFlag, env.charNames)
            print("--")
            print("Current Cumulative Reward =", cumulativeEpRew)

            print("----------")

            if done:
                print("Resetting Env")
                currNumEp += 1
                print("Ep. # = ", currNumEp)
                print("Ep. Cumulative Rew # = ", cumulativeEpRew)
                cumulativeEpRewAll.append(cumulativeEpRew)
                cumulativeEpRew = 0.0

                observation = env.reset()
                showGymObs(observation, waitKey, vizFlag, env.charNames)

            if np.any([info["roundDone"], info["stageDone"], info["gameDone"], info["epDone"]]):

                if not hardCore:
                    # Position check
                    if env.playerSide == "P2":
                        if observation["P1"]["ownPosition"] != 1.0 or observation["P1"]["oppPosition"] != 0.0:
                            raise RuntimeError("Wrong starting positions:", observation["P1"]["ownPosition"],
                                                                            observation["P1"]["oppPosition"])
                    else:
                        if observation["P1"]["ownPosition"] != 0.0 or observation["P1"]["oppPosition"] != 1.0:
                            raise RuntimeError("Wrong starting positions:", observation["P1"]["ownPosition"],
                                                                            observation["P1"]["oppPosition"])

        print("Cumulative reward = ", cumulativeEpRewAll)
        print("Mean cumulative reward = ", np.mean(cumulativeEpRewAll))
        print("Std cumulative reward = ", np.std(cumulativeEpRewAll))

        env.close()

        if len(cumulativeEpRewAll) != maxNumEp:
            raise RuntimeError("Not run all episodes")

        if opt.continueGame <= 0.0:
            maxContinue = int(-opt.continueGame)
        else:
            maxContinue = 0

        if opt.gameId == "tektagt":
            maxContinue = (maxContinue + 1) * 0.7 - 1

        if opt.noAction == 1 and np.mean(cumulativeEpRewAll) > -2*(maxContinue+1)*env.maxDeltaHealth+0.001:
            raise RuntimeError("NoAction policy and average reward different than {} ({})".format(-2*(maxContinue+1)*env.maxDeltaHealth, np.mean(cumulativeEpRewAll)))

        print("ALL GOOD!")
    except Exception as e:
        print(e)
        print("ALL BAD")
