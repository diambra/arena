import sys, os, time, random
from copy import deepcopy
import numpy as np
from collections import deque
import cv2  # pytype:disable=import-error
cv2.ocl.setUseOpenCL(False)

import gym
from gym import spaces

# Functions
def WarpFrame3CFunc(obs, width, height):
    obs["frame"] = cv2.resize(obs["frame"], (width, height),
                              interpolation=cv2.INTER_LINEAR)[:,:,None]
    return obs

def WarpFrameFunc(obs, width, height):
    obs["frame"] = cv2.cvtColor(obs["frame"], cv2.COLOR_RGB2GRAY)
    return WarpFrame3CFunc(obs, width, height)

def ScaledFloatObsFunc(observation, observation_space):
    # Process all observations
    for k, v in observation.items():

        if isinstance(v, dict):
            ScaledFloatObsFunc(v, observation_space.spaces[k])
        else:
            vSpace = observation_space.spaces[k]
            if isinstance(vSpace, spaces.MultiDiscrete):
                nAct = observation_space.spaces[k].nvec[0]
                bufLen = observation_space.spaces[k].nvec.shape[0]
                actionsVector = np.zeros( ( bufLen * nAct), dtype=int)
                for iAct in range(bufLen):
                    actionsVector[iAct*nAct + observation[k][iAct] ] = 1
                observation[k] = actionsVector
            elif isinstance(vSpace, spaces.Discrete) and (vSpace.n > 2):
                varVector = np.zeros( (observation_space.spaces[k].n), dtype=np.float32)
                varVector[observation[k]] = 1
                observation[k] = varVector
            elif isinstance(vSpace, spaces.Box):
                highVal = np.max(vSpace.high)
                lowVal = np.min(vSpace.low)
                observation[k] = (np.array(observation[k]).astype(np.float32) - lowVal) / (highVal - lowVal)
    return observation

# Env Wrappers classes
class WarpFrame(gym.ObservationWrapper):
    def __init__(self, env, hwObsResize = [84, 84]):
        """
        Warp frames to 84x84 as done in the Nature paper and later work.
        :param env: (Gym Environment) the environment
        """
        print("Warning: for speedup, avoid frame warping wrappers,")
        print("         use environment's native frame wrapping through")
        print("        \"frameShape\" setting (see documentation for details).")
        gym.ObservationWrapper.__init__(self, env)
        self.width = hwObsResize[1]
        self.height = hwObsResize[0]
        self.observation_space.spaces["frame"] = spaces.Box(low=0, high=255,
                                                 shape=(self.height, self.width, 1),
                                                 dtype=self.observation_space["frame"].dtype)

    def observation(self, obs):
        """
        returns the current observation from a obs
        :param obs: environment obs
        :return: the observation
        """
        return WarpFrameFunc(obs, self.width, self.height)

class WarpFrame3C(gym.ObservationWrapper):
    def __init__(self, env, hwObsResize = [224, 224]):
        """
        Warp frames to 84x84 as done in the Nature paper and later work.
        :param env: (Gym Environment) the environment
        """
        print("Warning: for speedup, avoid frame warping wrappers,")
        print("         use environment's native frame wrapping through")
        print("        \"frameShape\" setting (see documentation for details).")
        gym.ObservationWrapper.__init__(self, env)
        self.width = hwObsResize[1]
        self.height = hwObsResize[0]
        self.observation_space.spaces["frame"] = spaces.Box(low=0, high=255,
                                                 shape=(self.height, self.width, 3),
                                                 dtype=self.observation_space["frame"].dtype)

    def observation(self, obs):
        """/
        returns the current observation from a obs
        :param obs: environment obs
        :return: the observation
        """
        return WarpFrame3CFunc(obs, self.width, self.height)


class FrameStack(gym.Wrapper):
    def __init__(self, env, nFrames):
        """Stack nFrames last frames.
        Returns lazy array, which is much more memory efficient.
        See Also
        --------
        stable_baselines.common.atari_wrappers.LazyFrames
        :param env: (Gym Environment) the environment
        :param nFrames: (int) the number of frames to stack
        """
        gym.Wrapper.__init__(self, env)
        self.nFrames = nFrames
        self.frames = deque([], maxlen=nFrames)
        shp = self.observation_space["frame"].shape
        self.observation_space.spaces["frame"] = spaces.Box(low=0, high=255,
                                                 shape=(shp[0], shp[1], shp[2] * nFrames),
                                                 dtype=self.observation_space["frame"].dtype)

    def reset(self, **kwargs):
        obs = self.env.reset(**kwargs)
        # Fill the stack upon reset to avoid black frames
        for _ in range(self.nFrames):
            self.frames.append(obs["frame"])

        obs["frame"] = self.getOb()
        return obs

    def step(self, action):
        obs, reward, done, info = self.env.step(action)
        self.frames.append(obs["frame"])

        # Add last obs nFrames - 1 times in case of new round / stage / continueGame
        if (info["roundDone"] or info["stageDone"] or info["gameDone"]) and not done:
            for _ in range(self.nFrames - 1):
                self.frames.append(obs["frame"])

        obs["frame"] = self.getOb()
        return obs, reward, done, info

    def getOb(self):
        assert len(self.frames) == self.nFrames
        return LazyFrames(list(self.frames))


class FrameStackDilated(gym.Wrapper):
    def __init__(self, env, nFrames, dilation):
        """Stack nFrames last frames with dilation factor.
        Returns lazy array, which is much more memory efficient.
        See Also
        --------
        stable_baselines.common.atari_wrappers.LazyFrames
        :param env: (Gym Environment) the environment
        :param nFrames: (int) the number of frames to stack
        :param dilation: (int) the dilation factor
        """
        gym.Wrapper.__init__(self, env)
        self.nFrames = nFrames
        self.dilation = dilation
        self.frames = deque([], maxlen=nFrames*dilation) # Keeping all nFrames*dilation in memory,
                                                          # then extract the subset given by the dilation factor
        shp = self.observation_space["frame"].shape
        self.observation_space.spaces["frame"] = spaces.Box(low=0, high=255,
                                                 shape=(shp[0], shp[1], shp[2] * nFrames),
                                                 dtype=self.observation_space["frame"].dtype)

    def reset(self, **kwargs):
        obs = self.env.reset(**kwargs)
        for _ in range(self.nFrames*self.dilation):
            self.frames.append(obs["frame"])
        obs["frame"] = self.getOb()
        return obs

    def step(self, action):
        obs, reward, done, info = self.env.step(action)
        self.frames.append(obs["frame"])

        # Add last obs nFrames - 1 times in case of new round / stage / continueGame
        if (info["roundDone"] or info["stageDone"] or info["gameDone"]) and not done:
            for _ in range(self.nFrames*self.dilation - 1):
                self.frames.append(obs["frame"])

        obs["frame"] = self.getOb()
        return obs, reward, done, info

    def getOb(self):
        framesSubset = list(self.frames)[self.dilation-1::self.dilation]
        assert len(framesSubset) == self.nFrames
        return LazyFrames(list(framesSubset))

class ActionsStack(gym.Wrapper):
    def __init__(self, env, nActionsStack, nPlayers=1):
        """Stack nActionsStack last actions.
        :param env: (Gym Environment) the environment
        :param nActionsStack: (int) the number of actions to stack
        """
        gym.Wrapper.__init__(self, env)
        self.nActionsStack = nActionsStack
        self.nPlayers = nPlayers
        self.moveActionStack = []
        self.attackActionStack = []
        for iPlayer in range(self.nPlayers):
            self.moveActionStack.append(deque([0 for i in range(nActionsStack)], maxlen=nActionsStack))
            self.attackActionStack.append(deque([0 for i in range(nActionsStack)], maxlen=nActionsStack))
            self.observation_space.spaces["P{}".format(iPlayer+1)].spaces["actions"].spaces["move"] =\
                    spaces.MultiDiscrete([self.nActions[iPlayer][0]]*nActionsStack)
            self.observation_space.spaces["P{}".format(iPlayer+1)].spaces["actions"].spaces["attack"] =\
                    spaces.MultiDiscrete([self.nActions[iPlayer][1]]*nActionsStack)

    def fillStack(self, value=0):
        # Fill the actions stack with no action after reset
        for _ in range(self.nActionsStack):
            for iPlayer in range(self.nPlayers):
                self.moveActionStack[iPlayer].append(value)
                self.attackActionStack[iPlayer].append(value)

    def reset(self, **kwargs):
        obs = self.env.reset(**kwargs)
        self.fillStack()

        for iPlayer in range(self.nPlayers):
            obs["P{}".format(iPlayer+1)]["actions"]["move"] = self.moveActionStack[iPlayer]
            obs["P{}".format(iPlayer+1)]["actions"]["attack"] = self.attackActionStack[iPlayer]
        return obs

    def step(self, action):
        obs, reward, done, info = self.env.step(action)
        for iPlayer in range(self.nPlayers):
            self.moveActionStack[iPlayer].append(obs["P{}".format(iPlayer+1)]["actions"]["move"])
            self.attackActionStack[iPlayer].append(obs["P{}".format(iPlayer+1)]["actions"]["attack"])

        # Add noAction for nActionsStack - 1 times in case of new round / stage / continueGame
        if (info["roundDone"] or info["stageDone"] or info["gameDone"]) and not done:
            self.fillStack()

        for iPlayer in range(self.nPlayers):
            obs["P{}".format(iPlayer+1)]["actions"]["move"] = self.moveActionStack[iPlayer]
            obs["P{}".format(iPlayer+1)]["actions"]["attack"] = self.attackActionStack[iPlayer]
        return obs, reward, done, info

class ScaledFloatObsNeg(gym.ObservationWrapper):
    def __init__(self, env):
        gym.ObservationWrapper.__init__(self, env)
        self.observation_space.spaces["frame"] = spaces.Box(low=-1.0, high=1.0,
                                                 shape=self.observation_space["frame"].shape,
                                                 dtype=np.float32)

    def observation(self, observation):
        # careful! This undoes the memory optimization, use
        # with smaller replay buffers only.
        observation["frame"] = (np.array(observation["frame"]).astype(np.float32) / 127.5) - 1.0
        return observation

# Recursive function to modify obs dict
def ScaledFloatObsSpaceFunc(obsDict):
    # Updating observation space dict
    for k, v in obsDict.spaces.items():

        if isinstance(v, spaces.dict.Dict):
            ScaledFloatObsSpaceFunc(v)
        else:
            if isinstance(v, spaces.MultiDiscrete):
                # One hot encoding x nStack
                nVal = v.nvec.shape[0]
                maxVal = v.nvec[0]
                obsDict.spaces[k] = spaces.MultiDiscrete([2]*(nVal*maxVal))
            elif isinstance(v, spaces.Discrete) and (v.n > 2):
                # One hot encoding
                obsDict.spaces[k] = spaces.MultiDiscrete([2]*(v.n))
            elif isinstance(v, spaces.Box):
                obsDict.spaces[k] = spaces.Box(low=0, high=1.0, shape=v.shape, dtype=np.float32)

class ScaledFloatObs(gym.ObservationWrapper):
    def __init__(self, env):
        gym.ObservationWrapper.__init__(self, env)

        self.originalObservationSpace = deepcopy(self.observation_space)
        ScaledFloatObsSpaceFunc(self.observation_space)

    def observation(self, observation):
        # careful! This undoes the memory optimization, use
        # with smaller replay buffers only.

        return ScaledFloatObsFunc(observation, self.originalObservationSpace)

class LazyFrames(object):
    def __init__(self, frames):
        """
        This object ensures that common frames between the observations are only stored once.
        It exists purely to optimize memory usage which can be huge for DQN's 1M frames replay
        buffers.
        This object should only be converted to np.ndarray before being passed to the model.
        :param frames: ([int] or [float]) environment frames
        """
        self.frames = frames
        self.out = None

    def force(self):
        if self.out is None:
            self.out = np.concatenate(self.frames, axis=2)
            self.frames = None
        return self.out

    def __array__(self, dtype=None):
        out = self.force()
        if dtype is not None:
            out = out.astype(dtype)
        return out

    def __len__(self):
        return len(self.force())

    def __getitem__(self, i):
        return self.force()[i]
