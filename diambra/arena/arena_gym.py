import numpy as np
import os
import sys
import cv2
import gymnasium as gym
import logging
from diambra.arena.utils.gym_utils import discrete_to_multi_discrete_action
from diambra.arena.engine.interface import DiambraEngine
from diambra.arena.env_settings import EnvironmentSettings1P, EnvironmentSettings2P
from typing import Union, Any, Dict, List
from diambra.engine import model, SpaceType

class DiambraGymBase(gym.Env):
    """Diambra Environment gymnasium base interface"""
    metadata = {"render_modes": ["human", "rgb_array"]}
    _frame = None
    _last_action = None
    reward_normalization_value = 1.0
    render_gui_started = False

    def __init__(self, env_settings: Union[EnvironmentSettings1P, EnvironmentSettings2P]):
        self.logger = logging.getLogger(__name__)
        super(DiambraGymBase, self).__init__()

        self.env_settings = env_settings

        # Launch DIAMBRA Engine
        self.arena_engine = DiambraEngine(env_settings.env_address, env_settings.grpc_timeout)

        # Send environment settings, retrieve environment info
        self.env_info = self.arena_engine.env_init(self.env_settings.get_pb_request(init=True))
        self.env_settings.finalize_init(self.env_info)

        # Settings log
        self.logger.info(self.env_settings)

        # N actions
        self.n_actions = [self.env_info.available_actions.n_moves, self.env_info.available_actions.n_attacks]

        # Actions tuples and dict
        move_tuple = ()
        move_dict = {}
        attack_tuple= ()
        attack_dict = {}

        for idx in range(len(self.env_info.available_actions.moves)):
            move_tuple += (self.env_info.available_actions.moves[idx].key,)
            move_dict[idx] = self.env_info.available_actions.moves[idx].label

        for idx in range(len(self.env_info.available_actions.attacks)):
            attack_tuple += (self.env_info.available_actions.attacks[idx].key,)
            attack_dict[idx] = self.env_info.available_actions.attacks[idx].label

        self.actions_tuples = (move_tuple, attack_tuple)
        self.print_actions_dict = [move_dict, attack_dict]

        # Maximum difference in players health
        for k in sorted(self.env_info.ram_states.keys()):
            if "health" in k:
                self.max_delta_health = self.env_info.ram_states[k].max - self.env_info.ram_states[k].min
                break

    # Return env action list
    def get_actions_tuples(self):
        return self.actions_tuples

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
        return [self.env_info.cumulative_reward_bounds.min / (self.reward_normalization_value),
                self.env_info.cumulative_reward_bounds.max / (self.reward_normalization_value)]

    # Reset the environment
    def reset(self, seed: int = None, options: Dict[str, Any] = None):
        self._last_action = [[0, 0], [0, 0]]
        if options is None:
            options = {}
        options["seed"] = seed
        request = self.env_settings.update_episode_settings(options)
        response = self.arena_engine.reset(request.episode_settings)
        return self._get_obs(response), self._get_info(response)

    # Rendering the environment
    def render(self, wait_key=1):
        if self.env_settings.render_mode == "human" and (sys.platform.startswith('linux') is False or 'DISPLAY' in os.environ):
            try:
                if (self.render_gui_started is False):
                    self.window_name = "[{}] DIAMBRA Arena - {} - ({})".format(
                        os.getpid(), self.env_settings.game_id, self.env_settings.rank)
                    cv2.namedWindow(self.window_name, cv2.WINDOW_GUI_NORMAL)
                    self.render_gui_started = True
                    wait_key = 100

                cv2.imshow(self.window_name, self._frame[:, :, ::-1])
                cv2.waitKey(wait_key)
                return True
            except:
                return False
        elif self.env_settings.render_mode == "rgb_array":
            return self._frame

    # Print observation details to the console
    def show_obs(self, observation, wait_key=1, viz=True, string="observation", key=None):
        if type(observation) == dict:
            for k, v in sorted(observation.items()):
                self.show_obs(v, wait_key=wait_key, viz=viz, string=string + "[\"{}\"]".format(k), key=k)
        else:
            if key != "frame":
                if "action" in key:
                    out_value = observation
                    additional_string = ": "
                    if isinstance(observation, (int, np.integer)) is False:
                        n_actions_stack = int(observation.size / (self.n_actions[0] if "move" in key else self.n_actions[1]))
                        out_value = np.reshape(observation, [n_actions_stack, -1])
                        additional_string = " (reshaped for visualization):\n"
                    print(string + "{}{}".format(additional_string, out_value))
                elif "own_char" in key or "opp_char" in key:
                    char_idx = observation if type(observation) == int else np.where(observation == 1)[0][0]
                    print(string + ": {} / {}".format(observation, self.env_info.characters_info.char_list[char_idx]))
                else:
                    print(string + ": {}".format(observation))
            else:
                print(string + ": shape {} - min {} - max {}".format(observation.shape, np.amin(observation), np.amax(observation)))

                if viz is True and (sys.platform.startswith('linux') is False or 'DISPLAY' in os.environ):
                    try:
                        norm_factor = 255 if np.amax(observation) > 1.0 else 1.0
                        for idx in range(observation.shape[2]):
                            cv2.imshow("[{}] Frame channel {}".format(os.getpid(), idx), observation[:, :, idx] / norm_factor)

                        cv2.waitKey(wait_key)
                    except:
                        pass

    # Closing the environment
    def close(self):
        # Close DIAMBRA Arena
        cv2.destroyAllWindows()
        self.arena_engine.close()

    def _get_ram_states_obs_dict(self):
        player_spec_dict = {}
        generic_dict = {}
        # Adding env additional observations (side-specific)
        for k, v in self.env_info.ram_states.items():
            if k.endswith("P1"):
                target_dict = player_spec_dict
                knew = "own_" + k[:-3]
            elif k.endswith("P2"):
                target_dict = player_spec_dict
                knew = "opp_" + k[:-3]
            else:
                target_dict = generic_dict
                knew = k

            if  v.type == SpaceType.BINARY or v.type == SpaceType.DISCRETE:
                target_dict[knew] = gym.spaces.Discrete(v.max + 1)
            elif v.type == SpaceType.BOX:
                target_dict[knew] = gym.spaces.Box(low=v.min, high=v.max, shape=(1,), dtype=np.int32)
            else:
                raise RuntimeError("Only Discrete (Binary/Categorical) | Box Spaces allowed")

        player_spec_dict["action_move"] = gym.spaces.Discrete(self.n_actions[0])
        player_spec_dict["action_attack"] = gym.spaces.Discrete(self.n_actions[1])

        return generic_dict, player_spec_dict

    # Get frame
    def _get_frame(self, response):
        self._frame = np.frombuffer(response.observation.frame, dtype='uint8').reshape(self.env_info.frame_shape.h, \
                                                                                       self.env_info.frame_shape.w, \
                                                                                       self.env_info.frame_shape.c)
        return self._frame

    # Get info
    def _get_info(self, response):
        info = dict(response.info.game_states)
        info["settings"] = self.env_settings.pb_model
        return info

    # Integrate player specific RAM states into observation
    def _player_specific_ram_states_integration(self, response, idx):
        player_spec_dict = {}
        generic_dict = {}

        # Adding env additional observations (side-specific)
        player_role = self.env_settings.pb_model.episode_settings.player_settings[idx].role
        for k, v in self.env_info.ram_states.items():
            if (k.endswith("P1") or k.endswith("P2")):
                target_dict = player_spec_dict
                if k[-2:] == player_role:
                    knew = "own_" + k[:-3]
                else:
                    knew = "opp_" + k[:-3]
            else:
                target_dict = generic_dict
                knew = k

            # Box spaces
            if v.type == SpaceType.BOX:
                target_dict[knew] = np.array([response.observation.ram_states[k]], dtype=np.int32)
            else:  # Discrete spaces (binary / categorical)
                target_dict[knew] = response.observation.ram_states[k]

        player_spec_dict["action_move"] = self._last_action[idx][0]
        player_spec_dict["action_attack"] = self._last_action[idx][1]

        return generic_dict, player_spec_dict

class DiambraGym1P(DiambraGymBase):
    """Diambra Environment gymnasium single agent interface"""
    def __init__(self, env_settings):
        super().__init__(env_settings)

        # Observation space
        # Dictionary
        observation_space_dict = {}
        observation_space_dict['frame'] = gym.spaces.Box(low=0, high=255, shape=(self.env_info.frame_shape.h,
                                                                             self.env_info.frame_shape.w,
                                                                             self.env_info.frame_shape.c),
                                                                      dtype=np.uint8)
        generic_obs_dict, player_obs_dict = self._get_ram_states_obs_dict()
        observation_space_dict.update(generic_obs_dict)
        observation_space_dict.update(player_obs_dict)
        self.observation_space = gym.spaces.Dict(observation_space_dict)

        # Action space
        # MultiDiscrete actions:
        # - Arrows -> One discrete set
        # - Buttons -> One discrete set
        # Discrete actions:
        # - Arrows U Buttons -> One discrete set
        # NB: use the convention NOOP = 0
        if env_settings.action_space == SpaceType.MULTI_DISCRETE:
            self.action_space = gym.spaces.MultiDiscrete(self.n_actions)
        elif env_settings.action_space == SpaceType.DISCRETE:
            self.action_space = gym.spaces.Discrete(self.n_actions[0] + self.n_actions[1] - 1)
        self.logger.debug("Using {} action space".format(SpaceType.Name(env_settings.action_space)))

    # Return the no-op action
    def get_no_op_action(self):
        if isinstance(self.action_space, gym.spaces.MultiDiscrete):
            return [0, 0]
        else:
            return 0

    # Step the environment
    def step(self, action: Union[int, List[int]]):
        # Defining move and attack actions P1/P2 as a function of action_space
        if isinstance(self.action_space, gym.spaces.MultiDiscrete):
            self._last_action[0] = action
        else:
            self._last_action[0] = list(discrete_to_multi_discrete_action(action, self.n_actions[0]))
        response = self.arena_engine.step(self._last_action)
        observation = self._get_obs(response)

        return observation, response.reward, response.info.game_states["episode_done"], False, self._get_info(response)

    def _get_obs(self, response):
        observation = {}
        observation["frame"] = self._get_frame(response)
        generic_obs_dict, player_obs_dict = self._player_specific_ram_states_integration(response, 0)
        observation.update(generic_obs_dict)
        observation.update(player_obs_dict)

        return observation

class DiambraGym2P(DiambraGymBase):
    """Diambra Environment gymnasium multi-agent interface"""
    def __init__(self, env_settings):
        super().__init__(env_settings)

        # Dictionary observation space
        observation_space_dict = {}
        observation_space_dict['frame'] = gym.spaces.Box(low=0, high=255,
                                                     shape=(self.env_info.frame_shape.h,
                                                            self.env_info.frame_shape.w,
                                                            self.env_info.frame_shape.c),
                                                     dtype=np.uint8)

        generic_obs_dict, player_obs_dict = self._get_ram_states_obs_dict()
        observation_space_dict.update(generic_obs_dict)
        observation_space_dict["agent_0"] = gym.spaces.Dict(player_obs_dict)
        observation_space_dict["agent_1"] = gym.spaces.Dict(player_obs_dict)

        self.observation_space = gym.spaces.Dict(observation_space_dict)

        # Action space
        # Dictionary
        action_spaces_values = {SpaceType.MULTI_DISCRETE: gym.spaces.MultiDiscrete(self.n_actions),
                                SpaceType.DISCRETE: gym.spaces.Discrete(self.n_actions[0] + self.n_actions[1] - 1)}
        action_space_dict = self._map_action_spaces_to_agents(action_spaces_values)
        self.logger.debug("Using the following action spaces: {}".format(action_space_dict))
        self.action_space = gym.spaces.Dict(action_space_dict)

    # Return the no-op action
    def get_no_op_action(self):
        no_op_values = {SpaceType.MULTI_DISCRETE: [0, 0],
                        SpaceType.DISCRETE: 0}
        return self._map_action_spaces_to_agents(no_op_values)

    # Step the environment
    def step(self, actions: Dict[str, Union[int, List[int]]]):
        # NOTE: the assumption in current interface is that we have actions sorted as agent's order
        actions = sorted(actions.items())
        for idx, action in enumerate(actions):
            # Defining move and attack actions P1/P2 as a function of action_space
            if isinstance(self.action_space[action[0]], gym.spaces.MultiDiscrete):
                self._last_action[idx] = action[1]
            else:
                self._last_action[idx] = list(discrete_to_multi_discrete_action(action[1], self.n_actions[0]))
        response = self.arena_engine.step(self._last_action)
        observation = self._get_obs(response)

        return observation, response.reward, response.info.game_states["game_done"], False, self._get_info(response)

    def _map_action_spaces_to_agents(self, values_dict):
        out_dict = {}
        for idx, action_space in enumerate(self.env_settings.action_space):
            out_dict["agent_{}".format(idx)] = values_dict[action_space]

        return out_dict

    def _get_obs(self, response):
        observation = {}
        observation["frame"] = self._get_frame(response)
        for idx in range(self.env_settings.n_players):
            generic_obs_dict, player_obs_dict = self._player_specific_ram_states_integration(response, idx)
            observation["agent_{}".format(idx)] = player_obs_dict
        observation.update(generic_obs_dict)

        return observation