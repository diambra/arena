import cv2, sys, os, time
from os.path import expanduser
import numpy as np
import argparse

import diambraArena
from diambraArena.gymUtils import envSpacesSummary, discreteToMultiDiscreteAction

# Visualize Obs content
def showObs(observation, nActionsStack, waitKey=1, viz=True, charList=None):
    if type(observation) == dict:
        for k, v in observation.items():
            if k != "frame":
                if type(v) == dict:
                    for k2, v2 in v.items():
                        if type(v2) == dict:
                            for k3, v3 in v2.items():
                                print("observation[\"{}\"][\"{}\"][\"{}\"]:\n{}"\
                                      .format(k,k2,k3,np.reshape(v3, [nActionsStack,-1])))
                        elif "ownChar" in k2 or "oppChar" in k2:
                            print("observation[\"{}\"][\"{}\"]: {} / {}".format(k,k2,v2,\
                                                      charList[np.where(v2 == 1)[0][0]]))
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
        parser.add_argument('--recordTraj',     type=int,   default=0,          help='If to record trajectories (0=False)')
        parser.add_argument('--hardCore',       type=int,   default=0,          help='Hard core mode (0=False)')
        parser.add_argument('--interactiveViz', type=int,   default=0,          help='Interactive Visualization (0=False)')
        parser.add_argument('--libPath',        type=str,   default="",         help='Path to diambraEnvLib')
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

        # Recording kwargs
        trajRecKwargs = {}
        trajRecKwargs["userName"] = "Alex"
        trajRecKwargs["filePath"] = os.path.join( homeDir, "DIAMBRA/trajRecordings", opt.gameId)
        trajRecKwargs["ignoreP2"] = 0
        trajRecKwargs["commitHash"] = "0000000"

        if opt.recordTraj == 0:
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

        envId = opt.gameId + "_randomTestWrappers"
        hardCore = False if opt.hardCore == 0 else True
        env = diambraArena.make(envId, diambraKwargs, diambraGymKwargs, 
                                wrapperKwargs, trajRecKwargs, 
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
            showObs(observation, wrapperKwargs["actionsStack"], waitKey, vizFlag, charList=env.charNames)
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
                showObs(observation, wrapperKwargs["actionsStack"], waitKey, vizFlag, charList=env.charNames)

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

                    obs = observation["frame"]
                else:
                    obs = observation

                # Frames equality check
                for frameIdx in range(obs.shape[2]-1):
                    if np.any(obs[:,:,frameIdx] != obs[:,:,frameIdx+1]):
                        raise RuntimeError("Frames inside observation after round/stage/game/episode done are not equal. Dones =",
                                           info["roundDone"], info["stageDone"], info["gameDone"], info["epDone"])

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

        if opt.noAction == 1 and np.mean(cumulativeEpRewAll) > -(maxContinue+1)*3.999:
            raise RuntimeError("NoAction policy and average reward different than {} ({})".format(-(maxContinue+1)*4, np.mean(cumulativeEpRewAll)))

        print("ALL GOOD!")
    except Exception as e:
        print(e)
        print("ALL BAD")
