from gym import spaces
import gym
from copy import deepcopy
import numpy as np
from collections import deque
from collections.abc import Mapping
import cv2  # pytype:disable=import-error
cv2.ocl.setUseOpenCL(False)

# Env Wrappers classes
class WarpFrame(gym.ObservationWrapper):
    def __init__(self, env, hw_obs_resize=[84, 84]):
        """
        Warp frames to 84x84 as done in the Nature paper and later work.
        :param env: (Gym Environment) the environment
        """
        env.logger.warning("Warning: for speedup, avoid frame warping wrappers, use environment's " +
                           "native frame wrapping through \"frame_shape\" setting (see documentation for details)")
        gym.ObservationWrapper.__init__(self, env)
        self.width = hw_obs_resize[1]
        self.height = hw_obs_resize[0]
        self.observation_space.spaces["frame"] = spaces.Box(low=0, high=255,
                                                            shape=(self.height, self.width, 1),
                                                            dtype=self.observation_space["frame"].dtype)

    def observation(self, obs):
        """
        returns the current observation from a obs
        :param obs: environment obs
        :return: the observation
        """
        obs["frame"] = cv2.cvtColor(obs["frame"], cv2.COLOR_RGB2GRAY)
        obs["frame"] = cv2.resize(obs["frame"], (self.width, self.height),
                                  interpolation=cv2.INTER_LINEAR)[:, :, None]
        return obs

class WarpFrame3C(gym.ObservationWrapper):
    def __init__(self, env, hw_obs_resize=[224, 224]):
        """
        Warp frames to 84x84 as done in the Nature paper and later work.
        :param env: (Gym Environment) the environment
        """
        env.logger.warning("Warning: for speedup, avoid frame warping wrappers, use environment's " +
                           "native frame wrapping through \"frame_shape\" setting (see documentation for details)")
        gym.ObservationWrapper.__init__(self, env)
        self.width = hw_obs_resize[1]
        self.height = hw_obs_resize[0]
        self.observation_space.spaces["frame"] = spaces.Box(low=0, high=255,
                                                            shape=(self.height, self.width, 3),
                                                            dtype=self.observation_space["frame"].dtype)

    def observation(self, obs):
        """
        returns the current observation from a obs
        :param obs: environment obs
        :return: the observation
        """
        obs["frame"] = cv2.resize(obs["frame"], (self.width, self.height),
                                  interpolation=cv2.INTER_LINEAR)[:, :, None]
        return obs


class FrameStack(gym.Wrapper):
    def __init__(self, env, n_frames):
        """Stack n_frames last frames.

        :param env: (Gym Environment) the environment
        :param n_frames: (int) the number of frames to stack
        """
        gym.Wrapper.__init__(self, env)
        self.n_frames = n_frames
        self.frames = deque([], maxlen=n_frames)
        shp = self.observation_space["frame"].shape
        self.observation_space.spaces["frame"] = spaces.Box(low=0, high=255,
                                                            shape=(shp[0], shp[1], shp[2] * n_frames),
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
        if ((info["round_done"] or info["stage_done"] or info["game_done"]) and not done):
            for _ in range(self.n_frames - 1):
                self.frames.append(obs["frame"])

        obs["frame"] = self.get_ob()
        return obs, reward, done, info

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
        shp = self.observation_space["frame"].shape
        self.observation_space.spaces["frame"] = spaces.Box(low=0, high=255,
                                                            shape=(shp[0], shp[1], shp[2] * n_frames),
                                                            dtype=self.observation_space["frame"].dtype)

    def reset(self, **kwargs):
        obs = self.env.reset(**kwargs)
        for _ in range(self.n_frames * self.dilation):
            self.frames.append(obs["frame"])
        obs["frame"] = self.get_ob()
        return obs

    def step(self, action):
        obs, reward, done, info = self.env.step(action)
        self.frames.append(obs["frame"])

        # Add last obs n_frames - 1 times in case of
        # new round / stage / continueGame
        if ((info["round_done"] or info["stage_done"] or info["game_done"]) and not done):
            for _ in range(self.n_frames * self.dilation - 1):
                self.frames.append(obs["frame"])

        obs["frame"] = self.get_ob()
        return obs, reward, done, info

    def get_ob(self):
        frames_subset = list(self.frames)[self.dilation - 1::self.dilation]
        assert len(frames_subset) == self.n_frames
        return np.concatenate(frames_subset, axis=2)


class ActionsStack(gym.Wrapper):
    def __init__(self, env, n_actions_stack):
        """Stack n_actions_stack last actions.
        :param env: (Gym Environment) the environment
        :param n_actions_stack: (int) the number of actions to stack
        """
        gym.Wrapper.__init__(self, env)
        self.n_actions_stack = n_actions_stack
        self.n_players = 1 if self.env.env_settings.player != "P1P2" else 2
        self.move_action_stack = []
        self.attack_action_stack = []
        for iplayer in range(self.n_players):
            self.move_action_stack.append(deque([0 for i in range(n_actions_stack)], maxlen=n_actions_stack))
            self.attack_action_stack.append(deque([0 for i in range(n_actions_stack)], maxlen=n_actions_stack))

        if self.n_players == 1:
            self.observation_space["P1"]["actions"]["move"] = spaces.MultiDiscrete([self.n_actions[0]] * n_actions_stack)
            self.observation_space["P1"]["actions"]["attack"] = spaces.MultiDiscrete([self.n_actions[1]] * n_actions_stack)
        else:
            for iplayer in range(self.n_players):
                self.observation_space["P{}".format(iplayer + 1)]["actions"]["move"] =\
                    spaces.MultiDiscrete([self.n_actions[iplayer][0]] * n_actions_stack)
                self.observation_space["P{}".format(iplayer + 1)]["actions"]["attack"] =\
                    spaces.MultiDiscrete([self.n_actions[iplayer][1]] * n_actions_stack)

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
                iplayer + 1)]["actions"]["move"] = np.array(self.move_action_stack[iplayer])
            obs["P{}".format(
                iplayer + 1)]["actions"]["attack"] = np.array(self.attack_action_stack[iplayer])
        return obs

    def step(self, action):
        obs, reward, done, info = self.env.step(action)
        for iplayer in range(self.n_players):
            self.move_action_stack[iplayer].append(
                obs["P{}".format(iplayer + 1)]["actions"]["move"])
            self.attack_action_stack[iplayer].append(
                obs["P{}".format(iplayer + 1)]["actions"]["attack"])

        # Add noAction for n_actions_stack - 1 times
        # in case of new round / stage / continueGame
        if ((info["round_done"] or info["stage_done"] or info["game_done"]) and not done):
            self.fill_stack()

        for iplayer in range(self.n_players):
            obs["P{}".format(
                iplayer + 1)]["actions"]["move"] = np.array(self.move_action_stack[iplayer])
            obs["P{}".format(
                iplayer + 1)]["actions"]["attack"] = np.array(self.attack_action_stack[iplayer])
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
        observation["frame"] = observation["frame"] / 127.5 - 1.0
        return observation


class ScaledFloatObs(gym.ObservationWrapper):
    def __init__(self, env, exclude_image_scaling=False, process_discrete_binary=False):
        gym.ObservationWrapper.__init__(self, env)

        self.exclude_image_scaling = exclude_image_scaling
        self.process_discrete_binary = process_discrete_binary

        self.original_observation_space = deepcopy(self.observation_space)
        self.scaled_float_obs_space_func(self.observation_space)

    # Recursive function to modify obs space dict
    # FIXME: this can probably be dropped with gym >= 0.21 and only use the next one, here for SB2 compatibility
    def scaled_float_obs_space_func(self, obs_dict):
        # Updating observation space dict
        for k, v in obs_dict.spaces.items():

            if isinstance(v, spaces.dict.Dict):
                self.scaled_float_obs_space_func(v)
            else:
                if isinstance(v, spaces.MultiDiscrete):
                    # One hot encoding x nStack
                    n_val = v.nvec.shape[0]
                    max_val = v.nvec[0]
                    obs_dict.spaces[k] = spaces.MultiBinary(n_val * max_val)
                elif isinstance(v, spaces.Discrete) and (v.n > 2 or self.process_discrete_binary is True):
                    # One hot encoding
                    obs_dict.spaces[k] = spaces.MultiBinary(v.n)
                elif isinstance(v, spaces.Box) and (self.exclude_image_scaling is False or len(v.shape) < 3):
                    obs_dict.spaces[k] = spaces.Box(low=0.0, high=1.0, shape=v.shape, dtype=np.float32)

    # Recursive function to modify obs dict
    def scaled_float_obs_func(self, observation, observation_space):

        # Process all observations
        for k, v in observation.items():

            if isinstance(v, dict):
                self.scaled_float_obs_func(v, observation_space.spaces[k])
            else:
                v_space = observation_space.spaces[k]
                if isinstance(v_space, spaces.MultiDiscrete):
                    n_act = observation_space.spaces[k].nvec[0]
                    buf_len = observation_space.spaces[k].nvec.shape[0]
                    actions_vector = np.zeros((buf_len * n_act), dtype=np.uint8)
                    for iact in range(buf_len):
                        actions_vector[iact * n_act + observation[k][iact]] = 1
                    observation[k] = actions_vector
                elif isinstance(v_space, spaces.Discrete) and (v_space.n > 2 or self.process_discrete_binary is True):
                    var_vector = np.zeros((observation_space.spaces[k].n), dtype=np.uint8)
                    var_vector[observation[k]] = 1
                    observation[k] = var_vector
                elif isinstance(v_space, spaces.Box) and (self.exclude_image_scaling is False or len(v_space.shape) < 3):
                    high_val = np.max(v_space.high)
                    low_val = np.min(v_space.low)
                    observation[k] = np.array((observation[k] - low_val) / (high_val - low_val), dtype=np.float32)

        return observation

    def observation(self, observation):

        return self.scaled_float_obs_func(observation, self.original_observation_space)

def flatten_filter_obs_space_func(input_dictionary, filter_keys):
    _FLAG_FIRST = object()
    flattened_dict = {}

    def dummy_check(new_key):
        return True

    def check_filter(new_key):
        return new_key in filter_keys

    def visit(subdict, flattened_dict, partial_key, check_method):
        for k, v in subdict.spaces.items():
            new_key = k if partial_key == _FLAG_FIRST else partial_key + "_" + k
            if isinstance(v, Mapping) or isinstance(v, spaces.Dict):
                visit(v, flattened_dict, new_key, check_method)
            else:
                if check_method(new_key):
                    flattened_dict[new_key] = v

    if filter_keys is not None:
        visit(input_dictionary, flattened_dict, _FLAG_FIRST, check_filter)
    else:
        visit(input_dictionary, flattened_dict, _FLAG_FIRST, dummy_check)

    return flattened_dict

def flatten_filter_obs_func(input_dictionary, filter_keys):
    _FLAG_FIRST = object()
    flattened_dict = {}

    def dummy_check(new_key):
        return True

    def check_filter(new_key):
        return new_key in filter_keys

    def visit(subdict, flattened_dict, partial_key, check_method):
        for k, v in subdict.items():
            new_key = k if partial_key == _FLAG_FIRST else partial_key + "_" + k
            if isinstance(v, Mapping) or isinstance(v, spaces.Dict):
                visit(v, flattened_dict, new_key, check_method)
            else:
                if check_method(new_key):
                    flattened_dict[new_key] = v

    if filter_keys is not None:
        visit(input_dictionary, flattened_dict, _FLAG_FIRST, check_filter)
    else:
        visit(input_dictionary, flattened_dict, _FLAG_FIRST, dummy_check)

    return flattened_dict

class FlattenFilterDictObs(gym.ObservationWrapper):
    def __init__(self, env, filter_keys):
        gym.ObservationWrapper.__init__(self, env)

        self.filter_keys = filter_keys
        if (filter_keys is not None):
            self.filter_keys = list(set(filter_keys))
            if "frame" not in filter_keys:
                self.filter_keys += ["frame"]

        original_obs_space_keys = (flatten_filter_obs_space_func(self.observation_space, None)).keys()
        self.observation_space = spaces.Dict(flatten_filter_obs_space_func(self.observation_space, self.filter_keys))

        if filter_keys is not None:
            if (sorted(self.observation_space.spaces.keys()) != sorted(self.filter_keys)):
                raise Exception("Specified observation key(s) not found:",
                    "       Available key(s):", sorted(original_obs_space_keys),
                    "       Specified key(s):", sorted(self.filter_keys),
                    "       Key(s) not found:", sorted([key for key in self.filter_keys if key not in original_obs_space_keys]),
                )

    def observation(self, observation):

        return flatten_filter_obs_func(observation, self.filter_keys)
