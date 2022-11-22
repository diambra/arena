import numpy as np
import os
import sys
import cv2
import gym
import logging
from gym import spaces
from diambra.arena.utils.gym_utils import discrete_to_multi_discrete_action
from diambra.arena.engine.interface import DiambraEngine
from diambra.arena.env_settings import EnvironmentSettings1P, EnvironmentSettings2P
from typing import Union

# DIAMBRA Env Gym
class DiambraGymHardcoreBase(gym.Env):
    """Diambra Environment gym interface"""
    metadata = {'render.modes': ['human']}

    def __init__(self, env_settings: Union[EnvironmentSettings1P, EnvironmentSettings2P]):
        self.logger = logging.getLogger(__name__)
        super(DiambraGymHardcoreBase, self).__init__()

        self.reward_normalization_value = 1.0
        self.attack_but_combination = env_settings.attack_but_combination

        self.env_settings = env_settings
        self.render_gui_started = False

        # Launch DIAMBRA Arena
        self.arena_engine = DiambraEngine(env_settings.env_address, env_settings.grpc_timeout)

        # Send environment settings, retrieve environment info
        env_info_dict = self.arena_engine.env_init(self.env_settings)
        self.env_info_process(env_info_dict)
        self.player_side = self.env_settings.player
        self.difficulty = self.env_settings.difficulty

        # Settings log
        self.logger.info(self.env_settings)

        # Image as input:
        self.observation_space = spaces.Box(low=0, high=255,
                                            shape=(self.hwc_dim[0],
                                                   self.hwc_dim[1],
                                                   self.hwc_dim[2]),
                                            dtype=np.uint8)

    # Processing Environment info
    def env_info_process(self, env_info_dict):
        # N actions
        self.n_actions_but_comb = env_info_dict["n_actions"][0]
        self.n_actions_no_but_comb = env_info_dict["n_actions"][1]
        # N actions
        if self.env_settings.player == "P1P2":
            self.n_actions = [self.n_actions_but_comb, self.n_actions_but_comb]
            for idx in range(2):
                if self.attack_but_combination[idx] is False:
                    self.n_actions[idx] = self.n_actions_no_but_comb
        else:
            self.n_actions = self.n_actions_but_comb
            if self.attack_but_combination is False:
                self.n_actions = self.n_actions_no_but_comb

        # Frame height, width and channel dimensions
        self.hwc_dim = env_info_dict["frame_shape"]

        # Maximum difference in players health
        self.max_delta_health = env_info_dict["delta_health"]

        # Maximum number of stages (1P game vs COM)
        self.max_stage = env_info_dict["max_stage"]

        # Min-Max reward
        self.cumulative_reward_bounds = env_info_dict["cumulative_reward_bounds"]

        # Characters names list
        self.char_names = env_info_dict["char_list"]

        # Action list
        self.action_list = (tuple(env_info_dict["actions_list"][0]), tuple(env_info_dict["actions_list"][1]))

        # Action dict
        self.print_actions_dict = env_info_dict["actions_dict"]

        # Ram states map
        self.ram_states = {}
        for k in sorted(env_info_dict["ram_states"].keys()):
            self.ram_states[k] = [env_info_dict["ram_states"][k].type,
                                  env_info_dict["ram_states"][k].min,
                                  env_info_dict["ram_states"][k].max]

    # Return env action list
    def action_list(self):
        return self.action_list

    # Print Actions
    def print_actions(self):
        self.logger.info("Move actions:")
        for k, v in self.print_actions_dict[0].items():
            self.logger.info(" {}: {}".format(k, v))

        self.logger.info("Attack actions:")
        for k, v in self.print_actions_dict[1].items():
            self.logger.info(" {}: {}".format(k, v))

    # Return cumulative reward bounds for the environment
    def get_cumulative_reward_bounds(self):
        return [self.cumulative_reward_bounds[0] / (self.reward_normalization_value),
                self.cumulative_reward_bounds[1] / (self.reward_normalization_value)]

    # Step method to be implemented in derived classes
    def step(self, action):
        raise NotImplementedError()

    # Resetting the environment
    def reset(self):
        cv2.destroyAllWindows()
        self.render_gui_started = False
        self.frame, data, self.player_side = self.arena_engine.reset()
        return self.frame

    # Rendering the environment
    def render(self, mode='human', wait_key=1):

        if mode == "human" and (sys.platform.startswith('linux') is False or 'DISPLAY' in os.environ):
            try:
                if (self.render_gui_started is False):
                    self.window_name = "[{}] DIAMBRA Arena - {} - ({})".format(
                        os.getpid(), self.env_settings.game_id, self.env_settings.rank)
                    cv2.namedWindow(self.window_name, cv2.WINDOW_GUI_NORMAL)
                    self.render_gui_started = True
                    wait_key = 100

                cv2.imshow(self.window_name, self.frame[:, :, ::-1])
                cv2.waitKey(wait_key)
                return True
            except:
                return False
        elif mode == "rgb_array":
            return self.frame

    # Print observation details to the console
    def show_obs(self, observation, wait_key=1, viz=True):

        if type(observation) == dict:
            for k, v in observation.items():
                if k != "frame":
                    if type(v) == dict:
                        for k2, v2 in v.items():
                            if k2 == "actions":

                                for k3, v3 in v2.items():
                                    out_value = v3
                                    additional_string = ": "
                                    if type(v3) != int:
                                        if self.env_settings.player == "P1P2":
                                            n_actions = self.n_actions[0] if k == "P1" else self.n_actions[1]
                                        else:
                                            n_actions = self.n_actions
                                        n_actions_stack = int(self.observation_space[k][k2][k3].n / (n_actions[0] if k3 == "move" else n_actions[1]))
                                        out_value = np.reshape(v3, [n_actions_stack, -1])
                                        additional_string = " (reshaped for visualization):\n"
                                    print("observation[\"{}\"][\"{}\"][\"{}\"]{}{}".format(k, k2, k3, additional_string, out_value))
                            elif "ownChar" in k2 or "oppChar" in k2:
                                char_idx = v2 if type(v2) == int else np.where(v2 == 1)[0][0]
                                print("observation[\"{}\"][\"{}\"]: {} / {}".format(k, k2, v2, self.char_names[char_idx]))
                            else:
                                print("observation[\"{}\"][\"{}\"]: {}".format(k, k2, v2))
                    else:
                        print("observation[\"{}\"]: {}".format(k, v))
                else:
                    frame = observation["frame"]
                    print("observation[\"frame\"]: shape {} - min {} - max {}".format(frame.shape, np.amin(frame), np.amax(frame)))

            if viz:
                frame = observation["frame"]
        else:
            if viz:
                frame = observation

        if viz is True and (sys.platform.startswith('linux') is False or 'DISPLAY' in os.environ):
            try:
                norm_factor = 255 if np.amax(frame) > 1.0 else 1.0
                for idx in range(frame.shape[2]):
                    cv2.imshow("[{}] Frame channel {}".format(os.getpid(), idx), frame[:, :, idx] / norm_factor)

                cv2.waitKey(wait_key)
            except:
                pass

    # Closing the environment
    def close(self):
        # Close DIAMBRA Arena
        cv2.destroyAllWindows()
        self.arena_engine.close()

# DIAMBRA Gym base class for single player mode
class DiambraGymHardcore1P(DiambraGymHardcoreBase):
    def __init__(self, env_settings):
        super().__init__(env_settings)

        # Define action and observation space
        # They must be gym.spaces objects

        if env_settings.action_space == "multi_discrete":
            # MultiDiscrete actions:
            # - Arrows -> One discrete set
            # - Buttons -> One discrete set
            # NB: use the convention NOOP = 0, and buttons combinations
            #     can be prescripted:
            #     e.g. NOOP = [0], ButA = [1], ButB = [2], ButA+ButB = [3]
            #     or ignored:
            #     e.g. NOOP = [0], ButA = [1], ButB = [2]
            self.action_space = spaces.MultiDiscrete(self.n_actions)
            self.logger.debug("Using MultiDiscrete action space")
        elif env_settings.action_space == "discrete":
            # Discrete actions:
            # - Arrows U Buttons -> One discrete set
            # NB: use the convention NOOP = 0, and buttons combinations
            #     can be prescripted:
            #     e.g. NOOP = [0], ButA = [1], ButB = [2], ButA+ButB = [3]
            #     or ignored:
            #     e.g. NOOP = [0], ButA = [1], ButB = [2]
            self.action_space = spaces.Discrete(self.n_actions[0] + self.n_actions[1] - 1)
            self.logger.debug("Using Discrete action space")
        else:
            raise Exception("Not recognized action space: {}".format(env_settings.action_space))

    # Step the environment
    def step_complete(self, action):
        # Actions initialization
        mov_act = 0
        att_act = 0

        # Defining move and attack actions P1/P2 as a function of action_space

        if isinstance(self.action_space, gym.spaces.MultiDiscrete):
            mov_act = action[0]
            att_act = action[1]
        else:
            # Discrete to multidiscrete conversion
            mov_act, att_act = discrete_to_multi_discrete_action(
                action, self.n_actions[0])

        self.frame, reward, data = self.arena_engine.step_1p(mov_act, att_act)
        done = data["ep_done"]

        return self.frame, reward, done, data

    # Step the environment
    def step(self, action):

        self.frame, reward, done, data = self.step_complete(action)

        return self.frame, reward, done,\
            {"round_done": data["round_done"], "stage_done": data["stage_done"],
             "game_done": data["game_done"], "ep_done": data["ep_done"], "env_done": data["env_done"]}

# DIAMBRA Gym base class for two players mode
class DiambraGymHardcore2P(DiambraGymHardcoreBase):
    def __init__(self, env_settings):
        super().__init__(env_settings)

        # Define action spaces, they must be gym.spaces objects
        action_space_dict = {}
        for idx in range(2):
            if env_settings.action_space[idx] == "multi_discrete":
                action_space_dict["P{}".format(idx + 1)] =\
                    spaces.MultiDiscrete(self.n_actions[idx])
                self.logger.debug("Using MultiDiscrete action space for P{}".format(idx + 1))
            elif env_settings.action_space[idx] == "discrete":
                action_space_dict["P{}".format(idx + 1)] =\
                    spaces.Discrete(
                        self.n_actions[idx][0] + self.n_actions[idx][1] - 1)
                self.logger.debug("Using Discrete action space for P{}".format(idx + 1))
            else:
                raise Exception("Not recognized action space: {}".format(env_settings.action_space[idx]))

        self.action_space = spaces.Dict(action_space_dict)

    # Step the environment
    def step_complete(self, action):
        # Actions initialization
        mov_act_p1 = 0
        att_act_p1 = 0
        mov_act_p2 = 0
        att_act_p2 = 0

        # Defining move and attack actions P1/P2 as a function of action_space
        if isinstance(self.action_space["P1"], gym.spaces.MultiDiscrete):
            # P1
            mov_act_p1 = action[0]
            att_act_p1 = action[1]
            # P2
            # P2 MultiDiscrete Action Space
            if isinstance(self.action_space["P2"], gym.spaces.MultiDiscrete):
                mov_act_p2 = action[2]
                att_act_p2 = action[3]
            else:  # P2 Discrete Action Space
                mov_act_p2, att_act_p2 = discrete_to_multi_discrete_action(action[2], self.n_actions[1][0])

        else:  # P1 Discrete Action Space
            # P2
            # P2 MultiDiscrete Action Space
            if isinstance(self.action_space["P2"], gym.spaces.MultiDiscrete):
                # P1
                # Discrete to multidiscrete conversion
                mov_act_p1, att_act_p1 = discrete_to_multi_discrete_action(action[0], self.n_actions[0][0])
                mov_act_p2 = action[1]
                att_act_p2 = action[2]
            else:  # P2 Discrete Action Space
                # P1
                # Discrete to multidiscrete conversion
                mov_act_p1, att_act_p1 = discrete_to_multi_discrete_action(action[0], self.n_actions[0][0])
                mov_act_p2, att_act_p2 = discrete_to_multi_discrete_action(action[1], self.n_actions[1][0])

        self.frame, reward, data = self.arena_engine.step_2p(mov_act_p1, att_act_p1, mov_act_p2, att_act_p2)
        done = data["game_done"]
        # data["ep_done"]   = done

        return self.frame, reward, done, data

    # Step the environment
    def step(self, action):

        self.frame, reward, done, data = self.step_complete(action)

        return self.frame, reward, done,\
            {"round_done": data["round_done"], "stage_done": data["stage_done"],
             "game_done": data["game_done"], "ep_done": data["ep_done"], "env_done": data["env_done"]}

# DIAMBRA Gym base class providing frame and additional info as observations
class DiambraGym1P(DiambraGymHardcore1P):
    def __init__(self, env_settings):
        super().__init__(env_settings)

        # Dictionary observation space
        observation_space_dict = {}
        observation_space_dict['frame'] = spaces.Box(low=0, high=255,
                                                     shape=(self.hwc_dim[0],
                                                            self.hwc_dim[1],
                                                            self.hwc_dim[2]),
                                                     dtype=np.uint8)
        player_spec_dict = {}

        # Adding env additional observations (side-specific)
        for k, v in self.ram_states.items():

            if k == "stage":
                continue

            if k[-2:] == "P1":
                knew = "own" + k[:-2]
            else:
                knew = "opp" + k[:-2]

            # Discrete spaces (binary / categorical)
            if v[0] == 0 or v[0] == 2:
                player_spec_dict[knew] = spaces.Discrete(v[2] + 1)
            elif v[0] == 1:  # Box spaces
                player_spec_dict[knew] = spaces.Box(low=v[1], high=v[2],
                                                    shape=(1,), dtype=np.int32)
            else:
                raise RuntimeError(
                    "Only Discrete (Binary/Categorical) | Box Spaces allowed")

        actions_dict = {
            "move": spaces.Discrete(self.n_actions[0]),
            "attack": spaces.Discrete(self.n_actions[1])
        }

        player_spec_dict["actions"] = spaces.Dict(actions_dict)
        observation_space_dict["P1"] = spaces.Dict(player_spec_dict)
        observation_space_dict["stage"] = spaces.Box(low=self.ram_states["stage"][1],
                                                     high=self.ram_states["stage"][2],
                                                     shape=(1,), dtype=np.int8)

        self.observation_space = spaces.Dict(observation_space_dict)

    def ram_states_integration(self, frame, data):

        observation = {}
        observation["frame"] = frame
        observation["stage"] = np.array([data["stage"]], dtype=np.int8)

        player_spec_dict = {}

        # Adding env additional observations (side-specific)
        for k, v in self.ram_states.items():

            if k == "stage":
                continue

            if k[-2:] == self.player_side:
                knew = "own" + k[:-2]
            else:
                knew = "opp" + k[:-2]

            # Box spaces
            if v[0] == 1:
                player_spec_dict[knew] = np.array([data[k]], dtype=np.int32)
            else:  # Discrete spaces (binary / categorical)
                player_spec_dict[knew] = data[k]

        actions_dict = {
            "move": data["moveAction{}".format(self.player_side)],
            "attack": data["attackAction{}".format(self.player_side)],
        }

        player_spec_dict["actions"] = actions_dict
        observation["P1"] = player_spec_dict

        return observation

    def step(self, action):

        self.frame, reward, done, data = self.step_complete(action)

        observation = self.ram_states_integration(self.frame, data)

        return observation, reward, done,\
            {"round_done": data["round_done"], "stage_done": data["stage_done"],
             "game_done": data["game_done"], "ep_done": data["ep_done"], "env_done": data["env_done"]}

    # Reset the environment
    def reset(self):
        self.frame, data, self.player_side = self.arena_engine.reset()
        observation = self.ram_states_integration(self.frame, data)
        return observation

# DIAMBRA Gym base class providing frame and additional info as observations
class DiambraGym2P(DiambraGymHardcore2P):
    def __init__(self, env_settings):
        super().__init__(env_settings)

        # Dictionary observation space
        observation_space_dict = {}
        observation_space_dict['frame'] = spaces.Box(low=0, high=255,
                                                     shape=(self.hwc_dim[0],
                                                            self.hwc_dim[1],
                                                            self.hwc_dim[2]),
                                                     dtype=np.uint8)
        player_spec_dict = {}

        # Adding env additional observations (side-specific)
        for k, v in self.ram_states.items():

            if k == "stage":
                continue

            if k[-2:] == "P1":
                knew = "own" + k[:-2]
            else:
                knew = "opp" + k[:-2]

            if v[0] == 0 or v[0] == 2:  # Discrete spaces
                player_spec_dict[knew] = spaces.Discrete(v[2] + 1)
            elif v[0] == 1:  # Box spaces
                player_spec_dict[knew] = spaces.Box(low=v[1], high=v[2],
                                                    shape=(1,), dtype=np.int32)

            else:
                raise RuntimeError("Only Discrete and Box Spaces allowed")

        actions_dict = {
            "move": spaces.Discrete(self.n_actions[0][0]),
            "attack": spaces.Discrete(self.n_actions[0][1])
        }

        player_spec_dict["actions"] = spaces.Dict(actions_dict)
        player_dict_p1 = player_spec_dict.copy()
        observation_space_dict["P1"] = spaces.Dict(player_dict_p1)

        actions_dict = {
            "move": spaces.Discrete(self.n_actions[1][0]),
            "attack": spaces.Discrete(self.n_actions[1][1])
        }

        player_spec_dict["actions"] = spaces.Dict(actions_dict)
        player_dict_p2 = player_spec_dict.copy()
        observation_space_dict["P2"] = spaces.Dict(player_dict_p2)

        observation_space_dict["stage"] = spaces.Box(low=self.ram_states["stage"][1],
                                                     high=self.ram_states["stage"][2],
                                                     shape=(1,), dtype=np.int8)

        self.observation_space = spaces.Dict(observation_space_dict)

    def ram_states_integration(self, frame, data):

        observation = {}
        observation["frame"] = frame
        observation["stage"] = np.array([data["stage"]], dtype=np.int8)

        for ielem, elem in enumerate(["P1", "P2"]):

            player_spec_dict = {}

            # Adding env additional observations (side-specific)
            for k, v in self.ram_states.items():

                if k == "stage":
                    continue

                if k[-2:] == elem:
                    knew = "own" + k[:-2]
                else:
                    knew = "opp" + k[:-2]

                # Box spaces
                if v[0] == 1:
                    player_spec_dict[knew] = np.array([data[k]], dtype=np.int32)
                else:  # Discrete spaces (binary / categorical)
                    player_spec_dict[knew] = data[k]

            actions_dict = {
                "move": data["moveAction{}".format(elem)],
                "attack": data["attackAction{}".format(elem)],
            }

            player_spec_dict["actions"] = actions_dict
            observation[elem] = player_spec_dict

        return observation

    # Step the environment
    def step(self, action):

        self.frame, reward, done, data = self.step_complete(action)

        observation = self.ram_states_integration(self.frame, data)

        return observation, reward, done,\
            {"round_done": data["round_done"], "stage_done": data["stage_done"],
             "game_done": data["game_done"], "ep_done": data["ep_done"], "env_done": data["env_done"]}

    # Reset the environment
    def reset(self):
        self.frame, data, self.player_side = self.arena_engine.reset()
        observation = self.ram_states_integration(self.frame, data)
        return observation
