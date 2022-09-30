from gym import spaces
import gym
import numpy as np
from collections import deque
import cv2  # pytype:disable=import-error
cv2.ocl.setUseOpenCL(False)

# Env Wrappers classes
class WarpFrame(gym.ObservationWrapper):
    def __init__(self, env, hw_obs_resize=[84, 84]):
        """
        Warp frames to 84x84 as done in the Nature paper and later work.
        :param env: (Gym Environment) the environment
        """
        env.logger.warning("Warning: for speedup, avoid frame warping wrappers, use environment's "\
                           "native frame wrapping through \"frame_shape\" setting (see documentation for details)")
        gym.ObservationWrapper.__init__(self, env)
        self.width = hw_obs_resize[1]
        self.height = hw_obs_resize[0]
        self.observation_space = spaces.Box(low=0, high=255,
                                            shape=(self.height, self.width, 1),
                                            dtype=self.observation_space.dtype)

    def observation(self, frame):
        """
        returns the current observation from a frame
        :param frame: ([int] or [float]) environment frame
        :return: ([int] or [float]) the observation
        """
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        frame = cv2.resize(frame, (self.width, self.height),
                           interpolation=cv2.INTER_LINEAR)[:, :, None]
        return frame


class WarpFrame3C(gym.ObservationWrapper):
    def __init__(self, env, hw_obs_resize=[224, 224]):
        """
        Warp frames to 84x84 as done in the Nature paper and later work.
        :param env: (Gym Environment) the environment
        """
        env.logger.warning("Warning: for speedup, avoid frame warping wrappers, use environment's "\
                           "native frame wrapping through \"frame_shape\" setting (see documentation for details)")
        gym.ObservationWrapper.__init__(self, env)
        self.width = hw_obs_resize[1]
        self.height = hw_obs_resize[0]
        self.observation_space = spaces.Box(low=0, high=255,
                                            shape=(self.height, self.width, 3),
                                            dtype=self.observation_space.dtype)

    def observation(self, frame):
        """
        returns the current observation from a frame
        :param frame: ([int] or [float]) environment frame
        :return: ([int] or [float]) the observation
        """
        frame = cv2.resize(frame, (self.width, self.height),
                           interpolation=cv2.INTER_LINEAR)[:, :, None]
        return frame


class FrameStack(gym.Wrapper):
    def __init__(self, env, n_frames):
        """Stack n_frames last frames.

        :param env: (Gym Environment) the environment
        :param n_frames: (int) the number of frames to stack
        """
        gym.Wrapper.__init__(self, env)
        self.n_frames = n_frames
        self.frames = deque([], maxlen=n_frames)
        shp = self.observation_space.shape
        self.observation_space = spaces.Box(low=0, high=255,
                                            shape=(shp[0], shp[1], shp[2] * n_frames),
                                            dtype=self.observation_space.dtype)

    def reset(self, **kwargs):
        obs = self.env.reset(**kwargs)
        # Fill the stack upon reset to avoid black frames
        for _ in range(self.n_frames):
            self.frames.append(obs)

        return self.get_ob()

    def step(self, action):
        obs, reward, done, info = self.env.step(action)
        self.frames.append(obs)

        # Add last obs n_frames - 1 times in case of
        # new round / stage / continueGame
        if ((info["round_done"] or info["stage_done"] or info["game_done"]) and not done):
            for _ in range(self.n_frames - 1):
                self.frames.append(obs)

        return self.get_ob(), reward, done, info

    def get_ob(self):
        assert len(self.frames) == self.n_frames
        return np.concatenate(self.frames, axis=2)


class FrameStackDilated(gym.Wrapper):
    def __init__(self, env, n_frames, dilation):
        """Stack n_frames last frames with dilation factor.
        :param env: (Gym Environment) the environment
        :param n_frames: (int) the number of frames to stack
        :param dilation: (int) the dilation factor
        """
        gym.Wrapper.__init__(self, env)
        self.n_frames = n_frames
        self.dilation = dilation
        # Keeping all n_frames*dilation in memory,
        # then extract the subset given by the dilation factor
        self.frames = deque([], maxlen=n_frames * dilation)
        shp = self.observation_space.shape
        self.observation_space = spaces.Box(low=0, high=255,
                                            shape=(shp[0], shp[1], shp[2] * n_frames),
                                            dtype=self.observation_space.dtype)

    def reset(self, **kwargs):
        obs = self.env.reset(**kwargs)
        for _ in range(self.n_frames * self.dilation):
            self.frames.append(obs)
        return self.get_ob()

    def step(self, action):
        obs, reward, done, info = self.env.step(action)
        self.frames.append(obs)

        # Add last obs n_frames - 1 times in case of
        # new round / stage / continueGame
        if ((info["round_done"] or info["stage_done"] or info["game_done"]) and not done):
            for _ in range(self.n_frames * self.dilation - 1):
                self.frames.append(obs)

        return self.get_ob(), reward, done, info

    def get_ob(self):
        frames_subset = list(self.frames)[self.dilation - 1::self.dilation]
        assert len(frames_subset) == self.n_frames
        return np.concatenate(frames_subset, axis=2)


class ScaledFloatObsNeg(gym.ObservationWrapper):
    def __init__(self, env):
        gym.ObservationWrapper.__init__(self, env)
        self.observation_space = spaces.Box(low=-1.0, high=1.0,
            shape=self.observation_space.shape, dtype=np.float32)

    def observation(self, observation):
        # careful! This undoes the memory optimization, use
        # with smaller replay buffers only.
        return observation / 127.5 - 1.0


class ScaledFloatObs(gym.ObservationWrapper):
    def __init__(self, env):
        gym.ObservationWrapper.__init__(self, env)

        self.observation_space = spaces.Box(low=0, high=1.0,
                                            shape=self.observation_space.shape,
                                            dtype=np.float32)

    def observation(self, observation):

        return observation / 255.0
