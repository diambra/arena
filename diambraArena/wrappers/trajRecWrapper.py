import os
import numpy as np
import datetime

import gym
from diambraArena.gymUtils import gymObsDictSpaceToStandardDict,\
    ParallelPickleWriter

# Trajectory recorder wrapper


class TrajectoryRecorder(gym.Wrapper):
    def __init__(self, env, file_path, user_name,
                 ignore_p2, commit_hash="0000000"):
        """
        Record trajectories to use them for imitation learning
        :param env: (Gym Environment) the environment to wrap
        :param file_path: (str) file path specifying where to
               store the trajectory file
        """
        gym.Wrapper.__init__(self, env)
        self.file_path = file_path
        self.user_name = user_name
        self.ignore_p2 = ignore_p2
        self.frameShp = self.env.observation_space["frame"].shape
        self.commit_hash = commit_hash

        if (self.env.playerSide == "P1P2"):
            if ((self.env.attackButCombination[0] != self.env.attackButCombination[1])
                    or (self.env.actionSpace[0] != self.env.actionSpace[1])):
                print(self.env.actionSpace, self.env.attackButCombination)
                raise Exception("Different attack buttons combinations and/or "
                                "different action spaces not supported for 2P "
                                "experience recordings")

        print("Recording trajectories in \"{}\"".format(self.file_path))
        os.makedirs(self.file_path, exist_ok=True)

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
            self.lastFrameHist.append(obs["frame"][:, :, idx])

        # Store the whole obs without the frame
        tmp_obs = obs.copy()
        tmp_obs.pop("frame")
        self.addObsHist.append(tmp_obs)

        return obs

    def step(self, action):
        """
        Step the environment with the given action
        and add requested info to the observation
        :param action: ([int] or [float]) the action
        :return: new observation, reward, done, information
        """

        obs, reward, done, info = self.env.step(action)

        self.lastFrameHist.append(obs["frame"][:, :, self.frameShp[2]-1])

        # Add last obs nFrames - 1 times in case of
        # new round / stage / continue_game
        if ((info["roundDone"] or info["stageDone"] or info["gameDone"])
                and not done):
            for _ in range(self.frameShp[2]-1):
                self.lastFrameHist.append(
                    obs["frame"][:, :, self.frameShp[2]-1])

        # Store the whole obs without the frame
        tmp_obs = obs.copy()
        tmp_obs.pop("frame")
        self.addObsHist.append(tmp_obs)

        self.rewardsHist.append(reward)
        self.actionsHist.append(action)
        self.flagHist.append([info["roundDone"], info["stageDone"],
                              info["gameDone"], info["epDone"]])
        self.cumulativeRew += reward

        if done:
            to_save = {}
            to_save["commit_hash"] = self.commit_hash
            to_save["user_name"] = self.user_name
            to_save["playerSide"] = self.env.playerSide
            if self.env.playerSide != "P1P2":
                to_save["difficulty"] = self.env.difficulty
                to_save["actionSpace"] = self.env.actionSpace
            else:
                to_save["actionSpace"] = self.env.actionSpace[0]
            to_save["nActions"] = self.env.nActions[0]
            to_save["attackButComb"] = self.env.attackButCombination[0]
            to_save["frameShp"] = self.frameShp
            to_save["ignore_p2"] = self.ignore_p2
            to_save["charNames"] = self.env.charNames
            to_save["nActionsStack"] = int(
                self.env.observation_space["P1"]["actions"]["move"].nvec.shape[0]/self.env.nActions[0][0])
            to_save["epLen"] = len(self.rewardsHist)
            to_save["cumRew"] = self.cumulativeRew
            to_save["frames"] = self.lastFrameHist
            to_save["addObs"] = self.addObsHist
            to_save["rewards"] = self.rewardsHist
            to_save["actions"] = self.actionsHist
            to_save["doneFlags"] = self.flagHist
            to_save["observationSpaceDict"] = gymObsDictSpaceToStandardDict(
                self.env.observation_space)

            # Characters name
            # If 2P mode
            if self.env.playerSide == "P1P2" and self.ignore_p2 == 0:
                save_path = "mod" + str(self.ignore_p2) + "_" +\
                    self.env.playerSide + "_rew" +\
                    str(np.round(self.cumulativeRew, 3)) +\
                    "_" + datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            # If 1P mode
            else:
                save_path = "mod" + str(self.ignore_p2) + "_" +\
                           self.env.playerSide + "_diff" +\
                           str(self.env.difficulty) + "_rew" +\
                           str(np.round(self.cumulativeRew, 3)) + "_" +\
                           datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

            pickle_writer = ParallelPickleWriter(
                os.path.join(self.file_path, save_path), to_save)
            pickle_writer.start()

        return obs, reward, done, info
