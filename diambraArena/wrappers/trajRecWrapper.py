import sys, os, time, random
import numpy as np
from collections import deque
import datetime

import gym
from gym import spaces
from diambraArena.gymUtils import gymObsDictSpaceToStandardDict, parallelPickleWriter

# Trajectory recorder wrapper
class TrajectoryRecorder(gym.Wrapper):
    def __init__(self, env, filePath, userName, ignoreP2, commitHash="0000000"):
        """
        Record trajectories to use them for imitation learning
        :param env: (Gym Environment) the environment to wrap
        :param filePath: (str) file path specifying where to store the trajectory file
        """
        gym.Wrapper.__init__(self, env)
        self.filePath = filePath
        self.userName = userName
        self.ignoreP2 = ignoreP2
        self.frameShp = self.env.observation_space["frame"].shape
        self.commitHash = commitHash

        if (self.env.playerSide == "P1P2"):
            if ((self.env.attackButCombination[0] != self.env.attackButCombination[1]) or\
                (self.env.actionSpace[0] != self.env.actionSpace[1])):
                print(self.env.actionSpace, self.env.attackButCombination)
                raise Exception("Different attack buttons combinations and/or "\
                                "different action spaces not supported for 2P experience recordings")

        print("Recording trajectories in \"{}\"".format(self.filePath))
        os.makedirs(self.filePath, exist_ok = True)

    def reset(self, **kwargs):
        """
        Reset the environment and add requested info to the observation
        :return: observation
        """

        # Items to store
        self.lastFrameHist = []
        self.addObsHist = []
        self.rewardsHist = []
        self.actionsHist = []
        self.flagHist = []
        self.cumulativeRew = 0

        obs = self.env.reset(**kwargs)

        for idx in range(self.frameShp[2]):
            self.lastFrameHist.append(obs["frame"][:,:,idx])

        # Store the whole obs without the frame
        tmpObs = obs.copy()
        tmpObs.pop("frame")
        self.addObsHist.append(tmpObs)

        return obs

    def step(self, action):
        """
        Step the environment with the given action
        and add requested info to the observation
        :param action: ([int] or [float]) the action
        :return: new observation, reward, done, information
        """

        obs, reward, done, info = self.env.step(action)

        self.lastFrameHist.append(obs["frame"][:,:,self.frameShp[2]-1])

        # Add last obs nFrames - 1 times in case of new round / stage / continue_game
        if (info["roundDone"] or info["stageDone"] or info["gameDone"]) and not done:
            for _ in range(self.frameShp[2]-1):
                self.lastFrameHist.append(obs["frame"][:,:,self.frameShp[2]-1])

        # Store the whole obs without the frame
        tmpObs = obs.copy()
        tmpObs.pop("frame")
        self.addObsHist.append(tmpObs)

        self.rewardsHist.append(reward)
        self.actionsHist.append(action)
        self.flagHist.append([info["roundDone"], info["stageDone"],
                              info["gameDone"], info["epDone"]])
        self.cumulativeRew += reward

        if done:
            toSave = {}
            toSave["commitHash"]    = self.commitHash
            toSave["userName"]      = self.userName
            toSave["playerSide"]    = self.env.playerSide
            if self.env.playerSide != "P1P2":
                toSave["difficulty"]    = self.env.difficulty
                toSave["actionSpace"]   = self.env.actionSpace
            else:
                toSave["actionSpace"]   = self.env.actionSpace[0]
            toSave["nActions"]      = self.env.nActions[0]
            toSave["attackButComb"] = self.env.attackButCombination[0]
            toSave["frameShp"]      = self.frameShp
            toSave["ignoreP2"]      = self.ignoreP2
            toSave["charNames"]     = self.env.charNames
            toSave["partnerNames"]  = self.env.partnerNames
            toSave["nActionsStack"] = int(self.env.observation_space["P1"]["actions"]["move"].nvec.shape[0]/self.env.nActions[0][0])
            toSave["epLen"]         = len(self.rewardsHist)
            toSave["cumRew"]        = self.cumulativeRew
            toSave["frames"]        = self.lastFrameHist
            toSave["addObs"]        = self.addObsHist
            toSave["rewards"]       = self.rewardsHist
            toSave["actions"]       = self.actionsHist
            toSave["doneFlags"]     = self.flagHist
            toSave["observationSpaceDict"] = gymObsDictSpaceToStandardDict(self.env.observation_space)

            # Characters name
            # If 2P mode
            if self.env.playerSide == "P1P2" and self.ignoreP2 == 0:
                savePath = "mod" + str(self.ignoreP2) + "_" + self.env.playerSide +\
                           "_rew" + str(np.round(self.cumulativeRew, 3)) +\
                           "_" + datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            # If 1P mode
            else:
                savePath = "mod" + str(self.ignoreP2) + "_" + self.env.playerSide + \
                           "_diff" + str(self.env.difficulty)  + "_rew" + str(np.round(self.cumulativeRew, 3)) +\
                           "_" + datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

            pickleWriter = parallelPickleWriter(os.path.join(self.filePath, savePath), toSave)
            pickleWriter.start()

        return obs, reward, done, info
