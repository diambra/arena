from gym import spaces
import gym
from copy import deepcopy
import numpy as np
from collections import deque
import cv2  # pytype:disable=import-error
cv2.ocl.setUseOpenCL(False)


# Functions

def warp_frame_3c_func(obs, width, height):
    obs["frame"] = cv2.resize(obs["frame"], (width, height),
                              interpolation=cv2.INTER_LINEAR)[:, :, None]
    return obs


def warp_frame_func(obs, width, height):
    obs["frame"] = cv2.cvtColor(obs["frame"], cv2.COLOR_RGB2GRAY)
    return warp_frame_3c_func(obs, width, height)


def scaled_float_obs_func(observation, observation_space):
    # Process all observations
    for k, v in observation.items():

        if isinstance(v, dict):
            scaled_float_obs_func(v, observation_space.spaces[k])
        else:
            v_space = observation_space.spaces[k]
            if isinstance(v_space, spaces.MultiDiscrete):
                n_act = observation_space.spaces[k].nvec[0]
                buf_len = observation_space.spaces[k].nvec.shape[0]
                actions_vector = np.zeros((buf_len * n_act), dtype=int)
                for iact in range(buf_len):
                    actions_vector[iact*n_act + observation[k][iact]] = 1
                observation[k] = actions_vector
            elif isinstance(v_space, spaces.Discrete) and (v_space.n > 2):
                var_vector = np.zeros(
                    (observation_space.spaces[k].n), dtype=np.float32)
                var_vector[observation[k]] = 1
                observation[k] = var_vector
            elif isinstance(v_space, spaces.Box):
                high_val = np.max(v_space.high)
                low_val = np.min(v_space.low)
                observation[k] = (np.array(observation[k]).astype(
                    np.float32) - low_val) / (high_val - low_val)
    return observation

# Env Wrappers classes


class WarpFrame(gym.ObservationWrapper):
    def __init__(self, env, hw_obs_resize=[84, 84]):
        """
        Warp frames to 84x84 as done in the Nature paper and later work.
        :param env: (Gym Environment) the environment
        """
        print("Warning: for speedup, avoid frame warping wrappers,")
        print("         use environment's native frame wrapping through")
        print("        \"frameShape\" setting (see documentation for details)")
        gym.ObservationWrapper.__init__(self, env)
        self.width = hw_obs_resize[1]
        self.height = hw_obs_resize[0]
        self.observation_space.spaces["frame"] = spaces.Box(low=0, high=255,
                                                            shape=(
                                                                self.height, self.width, 1),
                                                            dtype=self.observation_space["frame"].dtype)

    def observation(self, obs):
        """
        returns the current observation from a obs
        :param obs: environment obs
        :return: the observation
        """
        return warp_frame_func(obs, self.width, self.height)


class WarpFrame3C(gym.ObservationWrapper):
    def __init__(self, env, hw_obs_resize=[224, 224]):
        """
        Warp frames to 84x84 as done in the Nature paper and later work.
        :param env: (Gym Environment) the environment
        """
        print("Warning: for speedup, avoid frame warping wrappers,")
        print("         use environment's native frame wrapping through")
        print("        \"frameShape\" setting (see documentation for details)")
        gym.ObservationWrapper.__init__(self, env)
        self.width = hw_obs_resize[1]
        self.height = hw_obs_resize[0]
        self.observation_space.spaces["frame"] = spaces.Box(low=0, high=255,
                                                            shape=(
                                                                self.height, self.width, 3),
                                                            dtype=self.observation_space["frame"].dtype)

    def observation(self, obs):
        """
        returns the current observation from a obs
        :param obs: environment obs
        :return: the observation
        """
        return warp_frame_3c_func(obs, self.width, self.height)


class FrameStack(gym.Wrapper):
    def __init__(self, env, n_frames):
        """Stack n_frames last frames.
        Returns lazy array, which is much more memory efficient.
        See Also
        --------
        stable_baselines.common.atari_wrappers.LazyFrames
        :param env: (Gym Environment) the environment
        :param n_frames: (int) the number of frames to stack
        """
        gym.Wrapper.__init__(self, env)
        self.n_frames = n_frames
        self.frames = deque([], maxlen=n_frames)
        shp = self.observation_space["frame"].shape
        self.observation_space.spaces["frame"] = spaces.Box(low=0, high=255,
                                                            shape=(
                                                                shp[0], shp[1], shp[2] * n_frames),
                                                            dtype=self.observation_space["frame"].dtype)

    def reset(self, **kwargs):
        obs = self.env.reset(**kwargs)
        # Fill the stack upon reset to avoid black frames
        for _ in range(self.n_frames):
            self.frames.append(obs["frame"])

        obs["frame"] = self.get_ob()
        return obs

    def step(self, action):
        obs, reward, done, info = self.env.step(action)
        self.frames.append(obs["frame"])

        # Add last obs n_frames - 1 times in case of
        # new round / stage / continueGame
        if ((info["round_done"] or info["stage_done"] or info["game_done"])
                and not done):
            for _ in range(self.n_frames - 1):
                self.frames.append(obs["frame"])

        obs["frame"] = self.get_ob()
        return obs, reward, done, info

    def get_ob(self):
        assert len(self.frames) == self.n_frames
        return LazyFrames(list(self.frames))


class FrameStackDilated(gym.Wrapper):
    def __init__(self, env, n_frames, dilation):
        """Stack n_frames last frames with dilation factor.
        Returns lazy array, which is much more memory efficient.
        See Also
        --------
        stable_baselines.common.atari_wrappers.LazyFrames
        :param env: (Gym Environment) the environment
        :param n_frames: (int) the number of frames to stack
        :param dilation: (int) the dilation factor
        """
        gym.Wrapper.__init__(self, env)
        self.n_frames = n_frames
        self.dilation = dilation
        # Keeping all n_frames*dilation in memory,
        # then extract the subset given by the dilation factor
        self.frames = deque([], maxlen=n_frames*dilation)
        shp = self.observation_space["frame"].shape
        self.observation_space.spaces["frame"] = spaces.Box(low=0, high=255,
                                                            shape=(
                                                                shp[0], shp[1], shp[2] * n_frames),
                                                            dtype=self.observation_space["frame"].dtype)

    def reset(self, **kwargs):
        obs = self.env.reset(**kwargs)
        for _ in range(self.n_frames*self.dilation):
            self.frames.append(obs["frame"])
        obs["frame"] = self.get_ob()
        return obs

    def step(self, action):
        obs, reward, done, info = self.env.step(action)
        self.frames.append(obs["frame"])

        # Add last obs n_frames - 1 times in case of
        # new round / stage / continueGame
        if ((info["round_done"] or info["stage_done"] or info["game_done"])
                and not done):
            for _ in range(self.n_frames*self.dilation - 1):
                self.frames.append(obs["frame"])

        obs["frame"] = self.get_ob()
        return obs, reward, done, info

    def get_ob(self):
        frames_subset = list(self.frames)[self.dilation-1::self.dilation]
        assert len(frames_subset) == self.n_frames
        return LazyFrames(list(frames_subset))


class ActionsStack(gym.Wrapper):
    def __init__(self, env, n_actions_stack, n_players=1):
        """Stack n_actions_stack last actions.
        :param env: (Gym Environment) the environment
        :param n_actions_stack: (int) the number of actions to stack
        """
        gym.Wrapper.__init__(self, env)
        self.n_actions_stack = n_actions_stack
        self.n_players = n_players
        self.move_action_stack = []
        self.attack_action_stack = []
        for iplayer in range(self.n_players):
            self.move_action_stack.append(
                deque([0 for i in range(n_actions_stack)], maxlen=n_actions_stack))
            self.attack_action_stack.append(
                deque([0 for i in range(n_actions_stack)], maxlen=n_actions_stack))
            self.observation_space.spaces["P{}".format(iplayer+1)].spaces["actions"].spaces["move"] =\
                spaces.MultiDiscrete([self.n_actions[iplayer][0]]*n_actions_stack)
            self.observation_space.spaces["P{}".format(iplayer+1)].spaces["actions"].spaces["attack"] =\
                spaces.MultiDiscrete([self.n_actions[iplayer][1]]*n_actions_stack)

    def fill_stack(self, value=0):
        # Fill the actions stack with no action after reset
        for _ in range(self.n_actions_stack):
            for iplayer in range(self.n_players):
                self.move_action_stack[iplayer].append(value)
                self.attack_action_stack[iplayer].append(value)

    def reset(self, **kwargs):
        obs = self.env.reset(**kwargs)
        self.fill_stack()

        for iplayer in range(self.n_players):
            obs["P{}".format(
                iplayer+1)]["actions"]["move"] = self.move_action_stack[iplayer]
            obs["P{}".format(
                iplayer+1)]["actions"]["attack"] = self.attack_action_stack[iplayer]
        return obs

    def step(self, action):
        obs, reward, done, info = self.env.step(action)
        for iplayer in range(self.n_players):
            self.move_action_stack[iplayer].append(
                obs["P{}".format(iplayer+1)]["actions"]["move"])
            self.attack_action_stack[iplayer].append(
                obs["P{}".format(iplayer+1)]["actions"]["attack"])

        # Add noAction for n_actions_stack - 1 times
        # in case of new round / stage / continueGame
        if ((info["round_done"] or info["stage_done"] or info["game_done"])
                and not done):
            self.fill_stack()

        for iplayer in range(self.n_players):
            obs["P{}".format(
                iplayer+1)]["actions"]["move"] = self.move_action_stack[iplayer]
            obs["P{}".format(
                iplayer+1)]["actions"]["attack"] = self.attack_action_stack[iplayer]
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
        observation["frame"] = (
            np.array(observation["frame"]).astype(np.float32) / 127.5) - 1.0
        return observation

# Recursive function to modify obs dict


def scaled_float_obs_space_func(obs_dict):
    # Updating observation space dict
    for k, v in obs_dict.spaces.items():

        if isinstance(v, spaces.dict.Dict):
            scaled_float_obs_space_func(v)
        else:
            if isinstance(v, spaces.MultiDiscrete):
                # One hot encoding x nStack
                n_val = v.nvec.shape[0]
                max_val = v.nvec[0]
                obs_dict.spaces[k] = spaces.MultiDiscrete([2]*(n_val*max_val))
            elif isinstance(v, spaces.Discrete) and (v.n > 2):
                # One hot encoding
                obs_dict.spaces[k] = spaces.MultiDiscrete([2]*(v.n))
            elif isinstance(v, spaces.Box):
                obs_dict.spaces[k] = spaces.Box(
                    low=0, high=1.0, shape=v.shape, dtype=np.float32)


class ScaledFloatObs(gym.ObservationWrapper):
    def __init__(self, env):
        gym.ObservationWrapper.__init__(self, env)

        self.original_observation_space = deepcopy(self.observation_space)
        scaled_float_obs_space_func(self.observation_space)

    def observation(self, observation):
        # careful! This undoes the memory optimization, use
        # with smaller replay buffers only.

        return scaled_float_obs_func(observation, self.original_observation_space)


class LazyFrames(object):
    def __init__(self, frames):
        """
        This object ensures that common frames between the observations
        are only stored once. It exists purely to optimize memory usage
        which can be huge for DQN's 1M frames replay buffers.
        This object should only be converted to np.ndarray
        before being passed to the model.
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
