import diambraArena
from diambraArena.gymUtils import envSpacesSummary, discreteToMultiDiscreteAction, showWrapObs
import argparse, time, os
from os.path import expanduser
import numpy as np

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
        parser.add_argument('--character1_3',   type=str,   default="Random",   help='Character P1_3 (Random)')
        parser.add_argument('--character2_3',   type=str,   default="Random",   help='Character P2_3 (Random)')
        parser.add_argument('--stepRatio',      type=int,   default=3,          help='Frame ratio')
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

        # Settings
        settings = {}
        settings["romsPath"] = opt.romsPath
        if opt.libPath != "":
            settings["libPath"]  = opt.libPath

        settings["player"]     = opt.player
        settings["characters"] = [[opt.character1, opt.character1_2, opt.character1_3],
                                  [opt.character2, opt.character2_2, opt.character2_3]]

        settings["stepRatio"] = opt.stepRatio
        settings["render"] = True
        settings["lockFps"] = False

        settings["continueGame"] = opt.continueGame
        settings["showFinal"]    = False

        settings["charOutfits"] = [2, 2]

        settings["actionSpace"] = [opt.actionSpace, opt.actionSpace]
        settings["attackButCombination"] = [opt.attButComb, opt.attButComb]
        if settings["player"] != "P1P2":
            settings["actionSpace"] = settings["actionSpace"][0]
            settings["attackButCombination"] = settings["attackButCombination"][0]

        # Recording settings
        trajRecSettings = {}
        trajRecSettings["userName"] = "Alex"
        trajRecSettings["filePath"] = os.path.join( homeDir, "DIAMBRA/trajRecordings", opt.gameId)
        trajRecSettings["ignoreP2"] = 0
        trajRecSettings["commitHash"] = "0000000"

        if opt.recordTraj == 0:
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

        nRounds = 2
        if opt.gameId == "kof98umh":
            nRounds = 3

        hardCore = False if opt.hardCore == 0 else True
        settings["hardCore"] = hardCore

        settings["envId"] = opt.gameId + "_randomTestWrappers"
        env = diambraArena.make(opt.gameId, settings, wrappersSettings, trajRecSettings,
                                seed=timeDepSeed)

        # Print environment obs and action spaces summary
        envSpacesSummary(env)

        observation = env.reset()

        cumulativeEpRew = 0.0
        cumulativeEpRewAll = []

        maxNumEp = opt.nEpisodes
        currNumEp = 0

        while currNumEp < maxNumEp:

            actions = [None, None]
            if settings["player"] != "P1P2":
                actions = env.action_space.sample()

                if opt.noAction == 1:
                    if settings["actionSpace"] == "multiDiscrete":
                        for iEl, _ in enumerate(actions):
                            actions[iEl] = 0
                    else:
                        actions = 0

                if settings["actionSpace"] == "discrete":
                    moveAction, attAction = discreteToMultiDiscreteAction(actions, env.nActions[0][0])
                else:
                    moveAction, attAction = actions[0], actions[1]

                print("(P1) {} {}".format(env.printActionsDict[0][moveAction],
                                          env.printActionsDict[1][attAction]))

            else:
                for idx in range(2):
                    actions[idx] = env.action_space["P{}".format(idx+1)].sample()

                    if opt.noAction == 1 and idx == 0:
                        if settings["actionSpace"][idx] == "multiDiscrete":
                            for iEl, _ in enumerate(actions[idx]):
                                actions[idx][iEl] = 0
                        else:
                            actions[idx] = 0

                    if settings["actionSpace"][idx] == "discrete":
                        moveAction, attAction = discreteToMultiDiscreteAction(actions[idx], env.nActions[idx][0])
                    else:
                        moveAction, attAction = actions[idx][0], actions[idx][1]

                    print("(P{}) {} {}".format(idx+1, env.printActionsDict[0][moveAction],
                                                      env.printActionsDict[1][attAction]))

            if settings["player"] == "P1P2" or settings["actionSpace"] != "discrete":
                actions = np.append(actions[0], actions[1])

            observation, reward, done, info = env.step(actions)

            cumulativeEpRew += reward
            print("action =", actions)
            print("reward =", reward)
            print("done =", done)
            for k, v in info.items():
                print("info[\"{}\"] = {}".format(k, v))
            showWrapObs(observation, wrappersSettings["actionsStack"], env.charNames, waitKey, vizFlag)
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
                showWrapObs(observation, wrappersSettings["actionsStack"], env.charNames, waitKey, vizFlag)

            if np.any([info["roundDone"], info["stageDone"], info["gameDone"], info["epDone"]]):

                if not hardCore:
                    # Side check
                    if env.playerSide == "P2":
                        if observation["P1"]["ownSide"] != 1.0 or observation["P1"]["oppSide"] != 0.0:
                            raise RuntimeError("Wrong starting sides:", observation["P1"]["ownSide"],
                                                                            observation["P1"]["oppSide"])
                    else:
                        if observation["P1"]["ownSide"] != 0.0 or observation["P1"]["oppSide"] != 1.0:
                            raise RuntimeError("Wrong starting sides:", observation["P1"]["ownSide"],
                                                                            observation["P1"]["oppSide"])

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

        if opt.noAction == 1 and np.mean(cumulativeEpRewAll) > -(maxContinue+1)*2*nRounds+0.001:
            raise RuntimeError("NoAction policy and average reward different than {} ({})".format(-(maxContinue+1)*2*nRounds, np.mean(cumulativeEpRewAll)))

        print("ALL GOOD!")
    except Exception as e:
        print(e)
        print("ALL BAD")
