import numpy as np
import cv2
import gym
from gym import spaces
from .utils.gym_utils import discrete_to_multi_discrete_action
from .engine.interface import DiambraEngine

# DIAMBRA Env Gym


class DiambraGymHardcoreBase(gym.Env):
    """Diambra Environment gym interface"""
    metadata = {'render.modes': ['human']}

    def __init__(self, env_settings):
        super(DiambraGymHardcoreBase, self).__init__()

        self.reward_normalization_value = 1.0
        self.attack_but_combination = env_settings["attack_but_combination"]

        self.env_settings = env_settings
        self.render_gui_started = False

        # Launch DIAMBRA Arena
        self.arena_engine = DiambraEngine(env_settings["env_address"])

        # Send environment settings, retrieve environment info
        env_info = self.arena_engine.env_init(self.env_settings)
        self.env_info_process(env_info)
        self.player_side = self.env_settings["player"]

        # Settings log
        print("Environment settings: --- ")
        print("")
        for key in sorted(self.env_settings):
            print("  \"{}\": {}".format(key, self.env_settings[key]))
        print("")
        print("------------------------- ")

        # Image as input:
        self.observation_space = spaces.Box(low=0, high=255,
                                            shape=(self.hwc_dim[0],
                                                   self.hwc_dim[1],
                                                   self.hwc_dim[2]),
                                            dtype=np.uint8)

    # Processing Environment info
    def env_info_process(self, env_info):
        # N actions
        self.n_actions_but_comb = [int(env_info[0]), int(env_info[1])]
        self.n_actions_no_but_comb = [int(env_info[2]), int(env_info[3])]
        # N actions
        self.n_actions = [self.n_actions_but_comb, self.n_actions_but_comb]
        for idx in range(2):
            if self.attack_but_combination[idx] is False:
                self.n_actions[idx] = self.n_actions_no_but_comb

        # Frame height, width and channel dimensions
        self.hwc_dim = [int(env_info[4]), int(env_info[5]), int(env_info[6])]
        self.arena_engine.set_frame_size(self.hwc_dim)

        # Maximum difference in players health
        self.max_delta_health = int(env_info[7]) - int(env_info[8])

        # Maximum number of stages (1P game vs COM)
        self.max_stage = int(env_info[9])

        # Game difficulty
        self.difficulty = int(env_info[10])

        # Number of characters of the game
        self.number_of_characters = int(env_info[11])

        # Number of characters used per round
        self.n_char_per_round = int(env_info[12])

        # Min-Max reward
        min_reward = int(env_info[13])
        max_reward = int(env_info[14])
        self.minmax_reward = [min_reward, max_reward]

        # Characters names list
        current_idx = 15
        self.char_names = []
        for idx in range(current_idx, current_idx + self.number_of_characters):
            self.char_names.append(env_info[idx])

        current_idx = current_idx + self.number_of_characters

        # Action list
        move_list = ()
        for idx in range(current_idx, current_idx + self.n_actions_but_comb[0]):
            move_list += (env_info[idx],)

        current_idx += self.n_actions_but_comb[0]

        attack_list = ()
        for idx in range(current_idx, current_idx + self.n_actions_but_comb[1]):
            attack_list += (env_info[idx],)

        current_idx += self.n_actions_but_comb[1]

        self.action_list = (move_list, attack_list)

        # Action dict
        move_dict = {}
        for idx in range(current_idx,
                         current_idx + 2*self.n_actions_but_comb[0], 2):
            move_dict[int(env_info[idx])] = env_info[idx+1]

        current_idx += 2*self.n_actions_but_comb[0]

        attack_dict = {}
        for idx in range(current_idx,
                         current_idx + 2*self.n_actions_but_comb[1], 2):
            attack_dict[int(env_info[idx])] = env_info[idx+1]

        self.print_actions_dict = [move_dict, attack_dict]

        current_idx += 2*self.n_actions_but_comb[1]

        # Additional Obs map
        number_of_add_obs = int(env_info[current_idx])
        current_idx += 1
        self.add_obs = {}
        for idx in range(number_of_add_obs):
            self.add_obs[env_info[current_idx]] = [int(env_info[current_idx+1]),
                                                   int(env_info[current_idx+2]),
                                                   int(env_info[current_idx+3])]
            current_idx += 4

    # Return env action list
    def action_list(self):
        return self.action_list

    # Print Actions
    def print_actions(self):
        print("Move actions:")
        for k, v in self.print_actions_dict[0].items():
            print(" {}: {}".format(k, v))

        print("Attack actions:")
        for k, v in self.print_actions_dict[1].items():
            print(" {}: {}".format(k, v))

    # Return min max rewards for the environment
    def get_min_max_reward(self):
        return [self.minmax_reward[0]/(self.reward_normalization_value),
                self.minmax_reward[1]/(self.reward_normalization_value)]

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

        if mode == "human":
            if (self.render_gui_started is False):
                self.window_name = "DIAMBRA Arena - {} - ({})".format(
                    self.env_settings["game_id"], self.env_settings["rank"])
                cv2.namedWindow(self.window_name, cv2.WINDOW_GUI_NORMAL)
                self.render_gui_started = True
                wait_key = 100

            cv2.imshow(self.window_name, self.frame[:, :, ::-1])
            cv2.waitKey(wait_key)
        elif mode == "rgb_array":
            return self.frame

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

        if env_settings["action_space"][0] == "multi_discrete":
            # MultiDiscrete actions:
            # - Arrows -> One discrete set
            # - Buttons -> One discrete set
            # NB: use the convention NOOP = 0, and buttons combinations
            #     can be prescripted:
            #     e.g. NOOP = [0], ButA = [1], ButB = [2], ButA+ButB = [3]
            #     or ignored:
            #     e.g. NOOP = [0], ButA = [1], ButB = [2]
            self.action_space = spaces.MultiDiscrete(self.n_actions[0])
            print("Using MultiDiscrete action space")
        elif env_settings["action_space"][0] == "discrete":
            # Discrete actions:
            # - Arrows U Buttons -> One discrete set
            # NB: use the convention NOOP = 0, and buttons combinations
            #     can be prescripted:
            #     e.g. NOOP = [0], ButA = [1], ButB = [2], ButA+ButB = [3]
            #     or ignored:
            #     e.g. NOOP = [0], ButA = [1], ButB = [2]
            self.action_space = spaces.Discrete(
                self.n_actions[0][0] + self.n_actions[0][1] - 1)
            print("Using Discrete action space")
        else:
            raise Exception(
                "Not recognized action space: {}".format(env_settings["action_space"][0]))

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
                action, self.n_actions[0][0])

        self.frame, data = self.arena_engine.step_1p(mov_act, att_act)
        reward = data["reward"]
        done = data["ep_done"]

        return self.frame, reward, done, data

    # Step the environment
    def step(self, action):

        self.frame, reward, done, data = self.step_complete(action)

        return self.frame, reward, done,\
            {"round_done": data["round_done"], "stage_done": data["stage_done"],
             "game_done": data["game_done"], "ep_done": data["ep_done"]}

# DIAMBRA Gym base class for two players mode


class DiambraGymHardcore2P(DiambraGymHardcoreBase):
    def __init__(self, env_settings):
        super().__init__(env_settings)

        # Define action spaces, they must be gym.spaces objects
        action_space_dict = {}
        for idx in range(2):
            if env_settings["action_space"][idx] == "multi_discrete":
                action_space_dict["P{}".format(idx+1)] =\
                    spaces.MultiDiscrete(self.n_actions[idx])
                print("Using MultiDiscrete action space for P{}".format(idx+1))
            elif env_settings["action_space"][idx] == "discrete":
                action_space_dict["P{}".format(idx+1)] =\
                    spaces.Discrete(
                        self.n_actions[idx][0] + self.n_actions[idx][1] - 1)
                print("Using Discrete action space for P{}".format(idx+1))
            else:
                raise Exception(
                    "Not recognized action space: {}".format(env_settings["action_space"][idx]))

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
                mov_act_p2, att_act_p2 = discrete_to_multi_discrete_action(
                    action[2], self.n_actions[1][0])

        else:  # P1 Discrete Action Space
            # P2
            # P2 MultiDiscrete Action Space
            if isinstance(self.action_space["P2"], gym.spaces.MultiDiscrete):
                # P1
                # Discrete to multidiscrete conversion
                mov_act_p1, att_act_p1 = discrete_to_multi_discrete_action(
                    action[0], self.n_actions[0][0])
                mov_act_p2 = action[1]
                att_act_p2 = action[2]
            else:  # P2 Discrete Action Space
                # P1
                # Discrete to multidiscrete conversion
                mov_act_p1, att_act_p1 = discrete_to_multi_discrete_action(
                    action[0], self.n_actions[0][0])
                mov_act_p2, att_act_p2 = discrete_to_multi_discrete_action(
                    action[1], self.n_actions[1][0])

        self.frame, data = self.arena_engine.step_2p(
            mov_act_p1, att_act_p1, mov_act_p2, att_act_p2)
        reward = data["reward"]
        done = data["game_done"]
        # data["ep_done"]   = done

        return self.frame, reward, done, data

    # Step the environment
    def step(self, action):

        self.frame, reward, done, data = self.step_complete(action)

        return self.frame, reward, done,\
            {"round_done": data["round_done"], "stage_done": data["stage_done"],
             "game_done": data["game_done"], "ep_done": data["ep_done"]}

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
        for k, v in self.add_obs.items():

            if k == "stage":
                continue

            if k[-2:] == "P1":
                knew = "own"+k[:-2]
            else:
                knew = "opp"+k[:-2]

            # Discrete spaces (binary / categorical)
            if v[0] == 0 or v[0] == 2:
                player_spec_dict[knew] = spaces.Discrete(v[2]+1)
            elif v[0] == 1:  # Box spaces
                player_spec_dict[knew] = spaces.Box(low=v[1], high=v[2],
                                                    shape=(), dtype=np.int32)

            else:
                raise RuntimeError(
                    "Only Discrete (Binary/Categorical) | Box Spaces allowed")

        actions_dict = {
            "move": spaces.Discrete(self.n_actions[0][0]),
            "attack": spaces.Discrete(self.n_actions[0][1])
        }

        player_spec_dict["actions"] = spaces.Dict(actions_dict)
        observation_space_dict["P1"] = spaces.Dict(player_spec_dict)
        observation_space_dict["stage"] = spaces.Box(low=self.add_obs["stage"][1],
                                                     high=self.add_obs["stage"][2],
                                                     shape=(), dtype=np.int8)

        self.observation_space = spaces.Dict(observation_space_dict)

    def add_obs_integration(self, frame, data):

        observation = {}
        observation["frame"] = frame
        observation["stage"] = data["stage"]

        player_spec_dict = {}

        # Adding env additional observations (side-specific)
        for k, v in self.add_obs.items():

            if k == "stage":
                continue

            if k[-2:] == self.player_side:
                knew = "own"+k[:-2]
            else:
                knew = "opp"+k[:-2]

            player_spec_dict[knew] = data[k]

        actions_dict = {
            "move": data["moveActionP1"],
            "attack": data["attackActionP1"],
        }

        player_spec_dict["actions"] = actions_dict
        observation["P1"] = player_spec_dict

        return observation

    def step(self, action):

        self.frame, reward, done, data = self.step_complete(action)

        observation = self.add_obs_integration(self.frame, data)

        return observation, reward, done,\
            {"round_done": data["round_done"], "stage_done": data["stage_done"],
             "game_done": data["game_done"], "ep_done": data["ep_done"]}

    # Reset the environment
    def reset(self):
        self.frame, data, self.player_side = self.arena_engine.reset()
        observation = self.add_obs_integration(self.frame, data)
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
        for k, v in self.add_obs.items():

            if k == "stage":
                continue

            if k[-2:] == "P1":
                knew = "own"+k[:-2]
            else:
                knew = "opp"+k[:-2]

            if v[0] == 0 or v[0] == 2:  # Discrete spaces
                player_spec_dict[knew] = spaces.Discrete(v[2]+1)
            elif v[0] == 1:  # Box spaces
                player_spec_dict[knew] = spaces.Box(low=v[1], high=v[2],
                                                    shape=(), dtype=np.int32)

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

        self.observation_space = spaces.Dict(observation_space_dict)

    def add_obs_integration(self, frame, data):

        observation = {}
        observation["frame"] = frame

        for ielem, elem in enumerate(["P1", "P2"]):

            player_spec_dict = {}

            # Adding env additional observations (side-specific)
            for k, v in self.add_obs.items():

                if k == "stage":
                    continue

                if k[-2:] == elem:
                    knew = "own"+k[:-2]
                else:
                    knew = "opp"+k[:-2]

                player_spec_dict[knew] = data[k]

            actions_dict = {
                "move": data["moveActionP{}".format(ielem+1)],
                "attack": data["attackActionP{}".format(ielem+1)],
            }

            player_spec_dict["actions"] = actions_dict
            observation[elem] = player_spec_dict

        return observation

    # Step the environment
    def step(self, action):

        self.frame, reward, done, data = self.step_complete(action)

        observation = self.add_obs_integration(self.frame, data)

        return observation, reward, done,\
            {"round_done": data["round_done"], "stage_done": data["stage_done"],
             "game_done": data["game_done"], "ep_done": data["ep_done"]}

    # Reset the environment
    def reset(self):
        self.frame, data, self.player_side = self.arena_engine.reset()
        observation = self.add_obs_integration(self.frame, data)
        return observation


def make_gym_env(env_settings):

    if env_settings["player"] != "P1P2":  # 1P Mode
        if env_settings["hardcore"]:
            env = DiambraGymHardcore1P(env_settings)
        else:
            env = DiambraGym1P(env_settings)
    else:  # 2P Mode
        if env_settings["hardcore"]:
            env = DiambraGymHardcore2P(env_settings)
        else:
            env = DiambraGym2P(env_settings)

    return env, env_settings["player"]
