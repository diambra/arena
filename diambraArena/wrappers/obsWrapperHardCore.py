import sys, os, time, random
import numpy as np
from collections import deque
import cv2  # pytype:disable=import-error
cv2.ocl.setUseOpenCL(False)

import gym
from gym import spaces

# Functions
def WarpFrame3CFunc(frame, width, height):
    frame = cv2.resize(frame, (width, height),
                       interpolation=cv2.INTER_LINEAR)[:,:,None]
    return frame

def WarpFrameFunc(frame, width, height):
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    return WarpFrame3CFunc(frame, width, height)

def ScaledFloatObsFunc(observation):
    return np.array(observation).astype(np.float32) / 255.0

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
        self.observation_space = spaces.Box(low=0, high=255, shape=(self.height, self.width, 1),
                                            dtype=env.observation_space.dtype)

    def observation(self, frame):
        """
        returns the current observation from a frame
        :param frame: ([int] or [float]) environment frame
        :return: ([int] or [float]) the observation
        """
        return WarpFrameFunc(frame, self.width, self.height)

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
        self.observation_space = spaces.Box(low=0, high=255, shape=(self.height, self.width, 3),
                                            dtype=env.observation_space.dtype)

    def observation(self, frame):
        """
        returns the current observation from a frame
        :param frame: ([int] or [float]) environment frame
        :return: ([int] or [float]) the observation
        """
        return WarpFrame3CFunc(frame, self.width, self.height)


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
        shp = env.observation_space.shape
        self.observation_space = spaces.Box(low=0, high=255, shape=(shp[0], shp[1], shp[2] * nFrames),
                                            dtype=env.observation_space.dtype)

    def reset(self, **kwargs):
        obs = self.env.reset(**kwargs)
        # Fill the stack upon reset to avoid black frames
        for _ in range(self.nFrames):
            self.frames.append(obs)

        return self.getOb()

    def step(self, action):
        obs, reward, done, info = self.env.step(action)
        self.frames.append(obs)

        # Add last obs nFrames - 1 times in case of new round / stage / continueGame
        if (info["roundDone"] or info["stageDone"] or info["gameDone"]) and not done:
            for _ in range(self.nFrames - 1):
                self.frames.append(obs)

        return self.getOb(), reward, done, info

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
        shp = env.observation_space.shape
        self.observation_space = spaces.Box(low=0, high=255, shape=(shp[0], shp[1], shp[2] * nFrames),
                                            dtype=env.observation_space.dtype)

    def reset(self, **kwargs):
        obs = self.env.reset(**kwargs)
        for _ in range(self.nFrames*self.dilation):
            self.frames.append(obs)
        return self.getOb()

    def step(self, action):
        obs, reward, done, info = self.env.step(action)
        self.frames.append(obs)

        # Add last obs nFrames - 1 times in case of new round / stage / continueGame
        if (info["roundDone"] or info["stageDone"] or info["gameDone"]) and not done:
            for _ in range(self.nFrames*self.dilation - 1):
                self.frames.append(obs)

        return self.getOb(), reward, done, info

    def getOb(self):
        framesSubset = list(self.frames)[self.dilation-1::self.dilation]
        assert len(framesSubset) == self.nFrames
        return LazyFrames(list(framesSubset))

class ScaledFloatObsNeg(gym.ObservationWrapper):
    def __init__(self, env):
        gym.ObservationWrapper.__init__(self, env)
        self.observation_space = spaces.Box(low=-1.0, high=1.0, shape=env.observation_space.shape, dtype=np.float32)

    def observation(self, observation):
        # careful! This undoes the memory optimization, use
        # with smaller replay buffers only.
        return (np.array(observation).astype(np.float32) / 127.5) - 1.0

class ScaledFloatObs(gym.ObservationWrapper):
    def __init__(self, env):
        gym.ObservationWrapper.__init__(self, env)
        self.observation_space = spaces.Box(low=0, high=1.0, shape=env.observation_space.shape, dtype=np.float32)

    def observation(self, observation):
        # careful! This undoes the memory optimization, use
        # with smaller replay buffers only.

        return ScaledFloatObsFunc(observation)

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
