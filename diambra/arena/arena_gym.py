import numpy as np
import os
import sys
import cv2
import gymnasium as gym
import logging
from diambra.arena.utils.gym_utils import discrete_to_multi_discrete_action
from diambra.arena.engine.interface import DiambraEngine
from diambra.arena.env_settings import EnvironmentSettings, EnvironmentSettingsMultiAgent
from typing import Union, Any, Dict, List
from diambra.engine import model, SpaceTypes

class DiambraGymBase(gym.Env):
    """Diambra Environment gymnasium base interface"""
    metadata = {"render_modes": ["human", "rgb_array"]}
    _frame = None
    reward_normalization_value = 1.0
    render_gui_started = False
    render_mode = None

    def __init__(self, env_settings: Union[EnvironmentSettings, EnvironmentSettingsMultiAgent]):
        self.logger = logging.getLogger(__name__)
        super(DiambraGymBase, self).__init__()

        self.env_settings = env_settings
        assert env_settings.render_mode is None or env_settings.render_mode in self.metadata["render_modes"]
        self.render_mode = env_settings.render_mode

        # Launch DIAMBRA Engine
        self.arena_engine = DiambraEngine(env_settings.env_address, env_settings.grpc_timeout)

        # Splash Screen
        if 'DISPLAY' in os.environ and env_settings.splash_screen is True:
            from .utils.splash_screen import SplashScreen
            SplashScreen()

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
        for k in sorted(self.env_info.ram_states_categories[model.RamStatesCategories.P1].ram_states.keys()):
            key_enum_name = model.RamStates.Name(k)
            if "health" in key_enum_name:
                self.max_delta_health = self.env_info.ram_states_categories[model.RamStatesCategories.P1].ram_states[k].max - \
                                        self.env_info.ram_states_categories[model.RamStatesCategories.P1].ram_states[k].min
                break

        # Observation space
        # Dictionary
        observation_space_dict = {}
        observation_space_dict['frame'] = gym.spaces.Box(low=0, high=255, shape=(self.env_info.frame_shape.h,
                                                                                 self.env_info.frame_shape.w,
                                                                                 self.env_info.frame_shape.c),
                                                                      dtype=np.uint8)

        # Adding RAM states observations
        for k, v in self.env_info.ram_states_categories.items():
            if k == model.RamStatesCategories.common:
                target_dict = observation_space_dict
            else:
                observation_space_dict[model.RamStatesCategories.Name(k)] = {}
                target_dict = observation_space_dict[model.RamStatesCategories.Name(k)]

            for k2, v2 in v.ram_states.items():
                if  v2.type == SpaceTypes.BINARY or v2.type == SpaceTypes.DISCRETE:
                    target_dict[model.RamStates.Name(k2)] = gym.spaces.Discrete(v2.max + 1)
                elif v2.type == SpaceTypes.BOX:
                    target_dict[model.RamStates.Name(k2)] = gym.spaces.Box(low=v2.min, high=v2.max, shape=(1,), dtype=np.int16)
                else:
                    raise RuntimeError("Only Discrete (Binary/Categorical) | Box Spaces allowed")

        for space_key in [model.RamStatesCategories.P1, model.RamStatesCategories.P2]:
            observation_space_dict[model.RamStatesCategories.Name(space_key)] = gym.spaces.Dict(observation_space_dict[model.RamStatesCategories.Name(space_key)])

        self.observation_space = gym.spaces.Dict(observation_space_dict)

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
        if options is None:
            options = {}
        options["seed"] = seed
        request = self.env_settings.update_episode_settings(options)
        response = self.arena_engine.reset(request.episode_settings)
        return self._get_obs(response), self._get_info(response)

    # Rendering the environment
    def render(self, wait_key=1):
        if self.render_mode == "human" and (sys.platform.startswith('linux') is False or 'DISPLAY' in os.environ):
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
        elif self.render_mode == "rgb_array":
            return self._frame

    # Print observation details to the console
    def show_obs(self, observation, wait_key=1, viz=True, string="observation", key=None, outermost=True):
        if type(observation) == dict:
            for k, v in sorted(observation.items()):
                self.show_obs(v, wait_key=wait_key, viz=viz, string=string + "[\"{}\"]".format(k), key=k, outermost=False)
        else:
            if key != "frame":
                if key.startswith("character"):
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
                    except:
                        pass

        if outermost is True and viz is True and (sys.platform.startswith('linux') is False or 'DISPLAY' in os.environ):
            try:
                cv2.waitKey(wait_key)
            except:
                pass

    # Closing the environment
    def close(self):
        # Close DIAMBRA Arena
        cv2.destroyAllWindows()
        self.arena_engine.close()

    # Get frame
    def _get_frame(self, response):
        self._frame = np.frombuffer(response.observation.frame, dtype='uint8').reshape(self.env_info.frame_shape.h, \
                                                                                       self.env_info.frame_shape.w, \
                                                                                       self.env_info.frame_shape.c)
        return self._frame

    # Get info
    def _get_info(self, response):
        info = {model.GameStates.Name(k): v for k, v in response.info.game_states.items()}
        info["settings"] = self.env_settings.pb_model
        return info

    def _get_obs(self, response):
        observation = {}
        observation["frame"] = self._get_frame(response)

        # Adding RAM states observations
        for k, v in self.env_info.ram_states_categories.items():
            if k == model.RamStatesCategories.common:
                target_dict = observation
            else:
                observation[model.RamStatesCategories.Name(k)] = {}
                target_dict = observation[model.RamStatesCategories.Name(k)]

            category_ram_states = response.observation.ram_states_categories[k]

            for k2, v2 in v.ram_states.items():
                # Box spaces
                if v2.type == SpaceTypes.BOX:
                    target_dict[model.RamStates.Name(k2)] = np.array([category_ram_states.ram_states[k2]])
                else:  # Discrete spaces (binary / categorical)
                    target_dict[model.RamStates.Name(k2)] = category_ram_states.ram_states[k2]

        return observation

class DiambraGym1P(DiambraGymBase):
    """Diambra Environment gymnasium single agent interface"""
    def __init__(self, env_settings: EnvironmentSettings):
        super().__init__(env_settings)

        # Action space
        # MultiDiscrete actions:
        # - Arrows -> One discrete set
        # - Buttons -> One discrete set
        # Discrete actions:
        # - Arrows U Buttons -> One discrete set
        # NB: use the convention NOOP = 0
        if env_settings.action_space == SpaceTypes.MULTI_DISCRETE:
            self.action_space = gym.spaces.MultiDiscrete(self.n_actions)
        elif env_settings.action_space == SpaceTypes.DISCRETE:
            self.action_space = gym.spaces.Discrete(self.n_actions[0] + self.n_actions[1] - 1)
        self.logger.debug("Using {} action space".format(SpaceTypes.Name(env_settings.action_space)))

    # Return the no-op action
    def get_no_op_action(self):
        if isinstance(self.action_space, gym.spaces.MultiDiscrete):
            return [0, 0]
        else:
            return 0

    # Step the environment
    def step(self, action: Union[int, List[int]]):
        # Defining move and attack actions P1/P2 as a function of action_space
        if isinstance(self.action_space, gym.spaces.Discrete):
            action = list(discrete_to_multi_discrete_action(action, self.n_actions[0]))
        response = self.arena_engine.step([action])

        return self._get_obs(response), response.reward, response.info.game_states[model.GameStates.episode_done], False, self._get_info(response)

class DiambraGym2P(DiambraGymBase):
    """Diambra Environment gymnasium multi-agent interface"""
    def __init__(self, env_settings: EnvironmentSettingsMultiAgent):
        super().__init__(env_settings)

        # Action space
        # Dictionary
        action_spaces_values = {SpaceTypes.MULTI_DISCRETE: gym.spaces.MultiDiscrete(self.n_actions),
                                SpaceTypes.DISCRETE: gym.spaces.Discrete(self.n_actions[0] + self.n_actions[1] - 1)}
        action_space_dict = self._map_action_spaces_to_agents(action_spaces_values)
        self.logger.debug("Using the following action spaces: {}".format(action_space_dict))
        self.action_space = gym.spaces.Dict(action_space_dict)

    # Return the no-op action
    def get_no_op_action(self):
        no_op_values = {SpaceTypes.MULTI_DISCRETE: [0, 0],
                        SpaceTypes.DISCRETE: 0}
        return self._map_action_spaces_to_agents(no_op_values)

    # Step the environment
    def step(self, actions: Dict[str, Union[int, List[int]]]):
        # NOTE: the assumption in current interface is that we have actions sorted as agent's order
        actions = sorted(actions.items())
        action_list = [[],[]]
        for idx, action in enumerate(actions):
            # Defining move and attack actions P1/P2 as a function of action_space
            if isinstance(self.action_space[action[0]], gym.spaces.MultiDiscrete):
                action_list[idx] = action[1]
            else:
                action_list[idx] = list(discrete_to_multi_discrete_action(action[1], self.n_actions[0]))
        response = self.arena_engine.step(action_list)

        return self._get_obs(response), response.reward, response.info.game_states[model.GameStates.game_done], False, self._get_info(response)

    def _map_action_spaces_to_agents(self, values_dict):
        out_dict = {}
        for idx, action_space in enumerate(self.env_settings.action_space):
            out_dict["agent_{}".format(idx)] = values_dict[action_space]

        return out_dict
