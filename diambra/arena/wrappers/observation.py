import gymnasium as gym
from copy import deepcopy
import numpy as np
from collections import deque
from collections.abc import Mapping
import cv2  # pytype:disable=import-error
cv2.ocl.setUseOpenCL(False)
from diambra.engine import Roles

# Env Wrappers classes
class GrayscaleFrame(gym.ObservationWrapper):
    def __init__(self, env):
        """
        :param env: (Gym Environment) the environment
        """
        gym.ObservationWrapper.__init__(self, env)
        self.unwrapped.logger.warning("Warning: for speedup, avoid frame warping wrappers, use environment's " +
                           "native frame grey scaling through \"frame_shape\" setting (see documentation for details)")

        self.width = self.observation_space.spaces["frame"].shape[1]
        self.height = self.observation_space.spaces["frame"].shape[0]
        self.observation_space.spaces["frame"] = gym.spaces.Box(low=0, high=255, shape=(self.height, self.width, 1),
                                                            dtype=self.observation_space["frame"].dtype)

    def observation(self, obs):
        """
        returns the current observation from a obs
        :param obs: environment obs
        :return: the observation
        """
        obs["frame"] = cv2.cvtColor(obs["frame"], cv2.COLOR_RGB2GRAY)
        return obs

class WarpFrame(gym.ObservationWrapper):
    def __init__(self, env, frame_shape=[84, 84]):
        """
        Warp frames to frame_shape resolution, not altering channels
        :param env: (Gym Environment) the environment
        """
        gym.ObservationWrapper.__init__(self, env)
        self.unwrapped.logger.warning("Warning: for speedup, avoid frame warping wrappers, use environment's " +
                           "native frame wrapping through \"frame_shape\" setting (see documentation for details)")

        self.width = frame_shape[1]
        self.height = frame_shape[0]
        channels = self.observation_space.spaces["frame"].shape[2]
        self.observation_space.spaces["frame"] = gym.spaces.Box(low=0, high=255, shape=(self.height, self.width, channels),
                                                            dtype=self.observation_space["frame"].dtype)

    def observation(self, obs):
        """
        returns the current observation from a obs
        :param obs: environment obs
        :return: the observation
        """
        obs["frame"] = cv2.resize(obs["frame"], (self.width, self.height), interpolation=cv2.INTER_LINEAR)[:, :, None]
        return obs

class FrameStack(gym.Wrapper):
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
        self.observation_space.spaces["frame"] = gym.spaces.Box(low=0, high=255,
                                                            shape=(shp[0], shp[1], shp[2] * n_frames),
                                                            dtype=self.observation_space["frame"].dtype)

    def reset(self, **kwargs):
        obs, info = self.env.reset(**kwargs)
        for _ in range(self.n_frames * self.dilation):
            self.frames.append(obs["frame"])
        obs["frame"] = self.get_ob()
        return obs, info

    def step(self, action):
        obs, reward, terminated, truncated, info = self.env.step(action)
        self.frames.append(obs["frame"])

        # Add last obs n_frames - 1 times in case of
        # new round / stage / continueGame
        if ((info["round_done"] or info["stage_done"] or info["game_done"]) and not (terminated or truncated)):
            for _ in range(self.n_frames * self.dilation - 1):
                self.frames.append(obs["frame"])

        obs["frame"] = self.get_ob()
        return obs, reward, terminated, truncated, info

    def get_ob(self):
        frames_subset = list(self.frames)[self.dilation - 1::self.dilation]
        assert len(frames_subset) == self.n_frames
        return np.concatenate(frames_subset, axis=2)

class AddLastActionToObservation(gym.Wrapper):
    def __init__(self, env):
        """Add last performed action to observation space
        :param env: (Gym Environment) the environment
        """
        gym.Wrapper.__init__(self, env)
        if self.unwrapped.env_settings.n_players == 1:
            self.observation_space = gym.spaces.Dict({
                **self.observation_space.spaces,
                "action": self.action_space,
            })
            def _add_last_action_to_obs_1p(obs, last_action):
                obs["action"] = last_action
                return obs
            self._add_last_action_to_obs = _add_last_action_to_obs_1p
        else:
            for idx in range(self.unwrapped.env_settings.n_players):
                action_dictionary = {}
                action_dictionary["action"] = self.action_space["agent_{}".format(idx)]
                self.observation_space = gym.spaces.Dict({
                    **self.observation_space.spaces,
                    "agent_{}".format(idx): gym.spaces.Dict(action_dictionary),
                })
            def _add_last_action_to_obs_2p(obs, last_action):
                for idx in range(self.unwrapped.env_settings.n_players):
                    action_dictionary = {}
                    action_dictionary["action"] = last_action["agent_{}".format(idx)]
                    obs["agent_{}".format(idx)] = action_dictionary
                return obs
            self._add_last_action_to_obs = _add_last_action_to_obs_2p

    def reset(self, **kwargs):
        obs, info = self.env.reset(**kwargs)
        return self._add_last_action_to_obs(obs, self.unwrapped.get_no_op_action()), info

    def step(self, action):
        obs, reward, terminated, truncated, info = self.env.step(action)
        return self._add_last_action_to_obs(obs, action), reward, terminated, truncated, info

class ActionsStack(gym.Wrapper):
    def __init__(self, env, n_actions_stack):
        """Stack n_actions_stack last actions.
        :param env: (Gym Environment) the environment
        :param n_actions_stack: (int) the number of actions to stack
        """
        gym.Wrapper.__init__(self, env)

        self.n_actions_stack = n_actions_stack
        no_op_action = self.unwrapped.get_no_op_action()

        if self.unwrapped.env_settings.n_players == 1:
            assert "action" in self.observation_space.spaces, "ActionsStack wrapper can be activated only "\
                                                              "when \"action\" info is in the observation space"

            if isinstance(self.action_space, gym.spaces.MultiDiscrete):
                self.action_stack = [deque(no_op_action * n_actions_stack, maxlen=n_actions_stack * 2)]
                action_space_size = list(self.observation_space["action"].nvec)
            else:
                self.action_stack = [deque([no_op_action] * n_actions_stack, maxlen=n_actions_stack)]
                action_space_size = [self.observation_space["action"].n]
            self.observation_space["action"] = gym.spaces.MultiDiscrete(action_space_size * n_actions_stack)

            if isinstance(self.action_space, gym.spaces.MultiDiscrete):
                def _add_action_to_stack_1p(action):
                    self.action_stack[0].append(action[0])
                    self.action_stack[0].append(action[1])
            else:
                def _add_action_to_stack_1p(action):
                    self.action_stack[0].append(action)
            self._add_action_to_stack = _add_action_to_stack_1p

            def _process_obs_1p(obs):
                obs["action"] = np.array(self.action_stack[0])
                return obs
            self._process_obs = _process_obs_1p
        else:
            self.action_stack = []
            assert "action" in self.observation_space["agent_0"].keys(), "ActionsStack wrapper can be activated only "\
                                                                         "when \"action\" info is in the observation space"
            for idx in range(self.unwrapped.env_settings.n_players):
                if isinstance(self.action_space["agent_{}".format(idx)], gym.spaces.MultiDiscrete):
                    self.action_stack.append(deque(no_op_action["agent_{}".format(idx)] * n_actions_stack, maxlen=n_actions_stack * 2))
                    action_space_size = list(self.observation_space["agent_{}".format(idx)]["action"].nvec)
                else:
                    self.action_stack.append(deque([no_op_action["agent_{}".format(idx)]] * n_actions_stack, maxlen=n_actions_stack))
                    action_space_size = [self.observation_space["agent_{}".format(idx)]["action"].n]
                self.observation_space["agent_{}".format(idx)]["action"] = gym.spaces.MultiDiscrete(action_space_size * n_actions_stack)

            def _add_action_to_stack_2p(action):
                for idx in range(self.unwrapped.env_settings.n_players):
                    if isinstance(self.action_space["agent_{}".format(idx)], gym.spaces.MultiDiscrete):
                        self.action_stack[idx].append(action["agent_{}".format(idx)][0])
                        self.action_stack[idx].append(action["agent_{}".format(idx)][1])
                    else:
                        self.action_stack[idx].append(action["agent_{}".format(idx)])
            self._add_action_to_stack = _add_action_to_stack_2p

            def _process_obs_2p(obs):
                for idx in range(self.unwrapped.env_settings.n_players):
                    obs["agent_{}".format(idx)]["action"] = np.array(self.action_stack[idx])
                return obs
            self._process_obs = _process_obs_2p

    def reset(self, **kwargs):
        obs, info = self.env.reset(**kwargs)
        self._fill_stack()
        return self._process_obs(obs), info

    def step(self, action):
        obs, reward, terminated, truncated, info = self.env.step(action)
        self._add_action_to_stack(action)

        # Add noAction for n_actions_stack - 1 times
        # in case of new round / stage / continueGame
        if ((info["round_done"] or info["stage_done"] or info["game_done"]) and not (terminated or truncated)):
            self._fill_stack()

        return self._process_obs(obs), reward, terminated, truncated, info

    def _fill_stack(self):
        no_op_action = self.unwrapped.get_no_op_action()
        for _ in range(self.n_actions_stack):
            self._add_action_to_stack(no_op_action)

class NormalizeObservation(gym.ObservationWrapper):
    def __init__(self, env, exclude_image_scaling=False, process_discrete_binary=False):
        gym.ObservationWrapper.__init__(self, env)

        self.exclude_image_scaling = exclude_image_scaling
        self.process_discrete_binary = process_discrete_binary

        self.original_observation_space = deepcopy(self.observation_space)
        self._obs_space_normalization_func(self.observation_space)

    def observation(self, observation):
        return self._obs_normalization_func(observation, self.original_observation_space)

    # Recursive function to modify obs space dict
    # FIXME: this can probably be dropped with gym >= 0.21 and only use the next one, here for SB2 compatibility
    def _obs_space_normalization_func(self, obs_dict):
        # Updating observation space dict
        for k, v in obs_dict.items():
            if isinstance(v, gym.spaces.Dict):
                self._obs_space_normalization_func(v)
            else:
                if isinstance(v, gym.spaces.MultiDiscrete):
                    # One hot encoding x nStack
                    obs_dict[k] = gym.spaces.MultiBinary(np.sum(v.nvec))
                elif isinstance(v, gym.spaces.Discrete) and (v.n > 2 or self.process_discrete_binary is True):
                    # One hot encoding
                    obs_dict[k] = gym.spaces.MultiBinary(v.n)
                elif isinstance(v, gym.spaces.Box) and (self.exclude_image_scaling is False or len(v.shape) < 3):
                    obs_dict[k] = gym.spaces.Box(low=0.0, high=1.0, shape=v.shape, dtype=np.float32)

    # Recursive function to modify obs dict
    def _obs_normalization_func(self, observation, observation_space):
        # Process all observations
        for k, v in observation.items():
            if isinstance(v, dict):
                self._obs_normalization_func(v, observation_space.spaces[k])
            else:
                v_space = observation_space[k]
                if isinstance(v_space, gym.spaces.MultiDiscrete):
                    actions_vector = np.zeros((np.sum(v_space.nvec)), dtype=np.uint8)
                    column_index = 0
                    for iact in range(v_space.nvec.shape[0]):
                        actions_vector[column_index + observation[k][iact]] = 1
                        column_index += v_space.nvec[iact]
                    observation[k] = actions_vector
                elif isinstance(v_space, gym.spaces.Discrete) and (v_space.n > 2 or self.process_discrete_binary is True):
                    var_vector = np.zeros((v_space.n), dtype=np.uint8)
                    var_vector[observation[k]] = 1
                    observation[k] = var_vector
                elif isinstance(v_space, gym.spaces.Box) and (self.exclude_image_scaling is False or len(v_space.shape) < 3):
                    high_val = np.max(v_space.high)
                    low_val = np.min(v_space.low)
                    observation[k] = np.array((observation[k] - low_val) / (high_val - low_val), dtype=np.float32)

        return observation

class RoleRelativeObservation(gym.Wrapper):
    def __init__(self, env):
        gym.Wrapper.__init__(self, env)

        new_observation_space = {}
        if self.unwrapped.env_settings.n_players == 1:
            for k, v in self.observation_space.items():
                if not isinstance(v, gym.spaces.Dict):
                    new_observation_space[k] = v
            new_observation_space["own"] = self.observation_space["P1"]
            new_observation_space["opp"] = self.observation_space["P1"]
        else:
            for k, v in self.observation_space.items():
                if not isinstance(v, gym.spaces.Dict) or k.startswith("agent_"):
                    new_observation_space[k] = v
            for idx in range(self.unwrapped.env_settings.n_players):
                new_observation_space["agent_{}".format(idx)]["own"] = self.observation_space["P1"]
                new_observation_space["agent_{}".format(idx)]["opp"] = self.observation_space["P1"]

        self.observation_space = gym.spaces.Dict(new_observation_space)

    def reset(self, **kwargs):
        obs, info = self.env.reset(**kwargs)
        if self.unwrapped.env_settings.n_players == 1:
            def _process_obs_1p(observation):
                new_observation = {}
                role_name = Roles.Name(info["settings"].episode_settings.player_settings[0].role)
                opponent_role_name = "P2" if role_name == "P1" else "P1"
                for k, v in observation.items():
                    if not isinstance(v, dict):
                        new_observation[k] = v
                new_observation["own"] = observation[role_name]
                new_observation["opp"] = observation[opponent_role_name]
                return new_observation
            self._process_obs = _process_obs_1p
        else:
            def _process_obs_2p(observation):
                new_observation = {}
                for k, v in observation.items():
                    if not isinstance(v, dict) or k.startswith("agent_"):
                        new_observation[k] = v
                for idx in range(self.unwrapped.env_settings.n_players):
                    role_name = Roles.Name(info["settings"].episode_settings.player_settings[idx].role)
                    opponent_role_name = "P2" if role_name == "P1" else "P1"
                    new_observation["agent_{}".format(idx)]["own"] = observation[role_name]
                    new_observation["agent_{}".format(idx)]["opp"] = observation[opponent_role_name]
                return new_observation
            self._process_obs = _process_obs_2p
        return self._process_obs(obs), info

    def step(self, action):
        obs, reward, terminated, truncated, info = self.env.step(action)
        return self._process_obs(obs), reward, terminated, truncated, info

class FlattenFilterDictObs(gym.ObservationWrapper):
    def __init__(self, env, filter_keys):
        gym.ObservationWrapper.__init__(self, env)

        self.filter_keys = filter_keys
        if len(filter_keys) != 0:
            self.filter_keys = list(set(filter_keys))
            if "frame" not in filter_keys:
                self.filter_keys += ["frame"]

        original_obs_space_keys = (flatten_filter_obs_space_func(self.observation_space, [])).keys()
        self.observation_space = gym.spaces.Dict(flatten_filter_obs_space_func(self.observation_space, self.filter_keys))

        if len(filter_keys) != 0:
            if (sorted(self.observation_space.spaces.keys()) != sorted(self.filter_keys)):
                raise Exception("Specified observation key(s) not found:",
                    "       Available key(s):", sorted(original_obs_space_keys),
                    "       Specified key(s):", sorted(self.filter_keys),
                    "       Key(s) not found:", sorted([key for key in self.filter_keys if key not in original_obs_space_keys]),
                )

    def observation(self, observation):
        return flatten_filter_obs_func(observation, self.filter_keys)

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
            if isinstance(v, Mapping) or isinstance(v, gym.spaces.Dict):
                visit(v, flattened_dict, new_key, check_method)
            else:
                if check_method(new_key):
                    flattened_dict[new_key] = v

    if len(filter_keys) != 0:
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
            if isinstance(v, Mapping) or isinstance(v, gym.spaces.Dict):
                visit(v, flattened_dict, new_key, check_method)
            else:
                if check_method(new_key):
                    flattened_dict[new_key] = v

    if len(filter_keys) != 0:
        visit(input_dictionary, flattened_dict, _FLAG_FIRST, check_filter)
    else:
        visit(input_dictionary, flattened_dict, _FLAG_FIRST, dummy_check)

    return flattened_dict