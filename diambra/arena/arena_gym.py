import numpy as np
import cv2
import gym
from gym import spaces
from diambra.arena.utils.gym_utils import discrete_to_multi_discrete_action
from diambra.arena.engine.interface import DiambraEngine

# DIAMBRA Env Gym


class DiambraGymHardCoreBase(gym.Env):
    """Diambra Environment gym interface"""
    metadata = {'render.modes': ['human']}

    def __init__(self, env_settings):
        super(DiambraGymHardCoreBase, self).__init__()

        self.rewardNormalizationValue = 1.0
        if env_settings["player"] != "P1P2":
            self.actionSpace = env_settings["actionSpace"][0]
        else:
            self.actionSpace = env_settings["actionSpace"]
        self.attackButCombination = env_settings["attackButCombination"]

        self.env_settings = env_settings
        self.renderGuiStarted = False

        # Launch DIAMBRA Arena
        self.arena_engine = DiambraEngine(env_settings["envAddress"])

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
                                            shape=(self.hwcDim[0],
                                                   self.hwcDim[1],
                                                   self.hwcDim[2]),
                                            dtype=np.uint8)

    # Processing Environment info
    def env_info_process(self, env_info):
        # N actions
        self.nActionsButComb = [int(env_info[0]), int(env_info[1])]
        self.nActionsNoButComb = [int(env_info[2]), int(env_info[3])]
        # N actions
        self.nActions = [self.nActionsButComb, self.nActionsButComb]
        for idx in range(2):
            if not self.attackButCombination[idx]:
                self.nActions[idx] = self.nActionsNoButComb

        # Frame height, width and channel dimensions
        self.hwcDim = [int(env_info[4]), int(env_info[5]), int(env_info[6])]
        self.arena_engine.set_frame_size(self.hwcDim)

        # Maximum difference in players health
        self.maxDeltaHealth = int(env_info[7]) - int(env_info[8])

        # Maximum number of stages (1P game vs COM)
        self.maxStage = int(env_info[9])

        # Game difficulty
        self.difficulty = int(env_info[10])

        # Number of characters of the game
        self.numberOfCharacters = int(env_info[11])

        # Number of characters used per round
        self.nCharPerRound = int(env_info[12])

        # Min-Max reward
        min_reward = int(env_info[13])
        max_reward = int(env_info[14])
        self.minmax_reward = [min_reward, max_reward]

        # Characters names list
        current_idx = 15
        self.charNames = []
        for idx in range(current_idx, current_idx + self.numberOfCharacters):
            self.charNames.append(env_info[idx])

        current_idx = current_idx + self.numberOfCharacters

        # Action list
        move_list = ()
        for idx in range(current_idx, current_idx + self.nActionsButComb[0]):
            move_list += (env_info[idx],)

        current_idx += self.nActionsButComb[0]

        attack_list = ()
        for idx in range(current_idx, current_idx + self.nActionsButComb[1]):
            attack_list += (env_info[idx],)

        current_idx += self.nActionsButComb[1]

        self.action_list = (move_list, attack_list)

        # Action dict
        move_dict = {}
        for idx in range(current_idx,
                         current_idx + 2*self.nActionsButComb[0], 2):
            move_dict[int(env_info[idx])] = env_info[idx+1]

        current_idx += 2*self.nActionsButComb[0]

        attack_dict = {}
        for idx in range(current_idx,
                         current_idx + 2*self.nActionsButComb[1], 2):
            attack_dict[int(env_info[idx])] = env_info[idx+1]

        self.print_actions_dict = [move_dict, attack_dict]

        current_idx += 2*self.nActionsButComb[1]

        # Additional Obs map
        number_of_add_obs = int(env_info[current_idx])
        current_idx += 1
        self.addObs = {}
        for idx in range(number_of_add_obs):
            self.addObs[env_info[current_idx]] = [int(env_info[current_idx+1]),
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
        return [self.minmax_reward[0]/(self.rewardNormalizationValue),
                self.minmax_reward[1]/(self.rewardNormalizationValue)]

    # Step method to be implemented in derived classes
    def step(self, action):
        raise NotImplementedError()

    # Resetting the environment
    def reset(self):
        cv2.destroyAllWindows()
        self.renderGuiStarted = False
        self.frame, data, self.player_side = self.arena_engine.reset()
        return self.frame

    # Rendering the environment
    def render(self, mode='human', wait_key=1):

        if mode == "human":
            if (self.renderGuiStarted is False):
                self.windowName = "DIAMBRA Arena - {} - ({})".format(
                    self.env_settings["gameId"], self.env_settings["rank"])
                cv2.namedWindow(self.windowName, cv2.WINDOW_GUI_NORMAL)
                self.renderGuiStarted = True
                wait_key = 100

            cv2.imshow(self.windowName, self.frame[:, :, ::-1])
            cv2.waitKey(wait_key)
        elif mode == "rgb_array":
            return self.frame

    # Closing the environment
    def close(self):
        # Close DIAMBRA Arena
        cv2.destroyAllWindows()
        self.arena_engine.close()

# DIAMBRA Gym base class for single player mode


class DiambraGymHardCore1P(DiambraGymHardCoreBase):
    def __init__(self, env_settings):
        super().__init__(env_settings)

        # Define action and observation space
        # They must be gym.spaces objects

        if self.actionSpace == "multiDiscrete":
            # MultiDiscrete actions:
            # - Arrows -> One discrete set
            # - Buttons -> One discrete set
            # NB: use the convention NOOP = 0, and buttons combinations
            #     can be prescripted:
            #     e.g. NOOP = [0], ButA = [1], ButB = [2], ButA+ButB = [3]
            #     or ignored:
            #     e.g. NOOP = [0], ButA = [1], ButB = [2]
            self.action_space = spaces.MultiDiscrete(self.nActions[0])
            print("Using MultiDiscrete action space")
        elif self.actionSpace == "discrete":
            # Discrete actions:
            # - Arrows U Buttons -> One discrete set
            # NB: use the convention NOOP = 0, and buttons combinations
            #     can be prescripted:
            #     e.g. NOOP = [0], ButA = [1], ButB = [2], ButA+ButB = [3]
            #     or ignored:
            #     e.g. NOOP = [0], ButA = [1], ButB = [2]
            self.action_space = spaces.Discrete(
                self.nActions[0][0] + self.nActions[0][1] - 1)
            print("Using Discrete action space")
        else:
            raise Exception(
                "Not recognized action space: {}".format(self.actionSpace))

    # Step the environment
    def step_complete(self, action):
        # Actions initialization
        mov_act = 0
        att_act = 0

        # Defining move and attack actions P1/P2 as a function of actionSpace
        if self.actionSpace == "multiDiscrete":
            mov_act = action[0]
            att_act = action[1]
        else:
            # Discrete to multidiscrete conversion
            mov_act, att_act = discrete_to_multi_discrete_action(
                action, self.nActions[0][0])

        self.frame, data = self.arena_engine.step_1p(mov_act, att_act)
        reward = data["reward"]
        done = data["epDone"]

        return self.frame, reward, done, data

    # Step the environment
    def step(self, action):

        self.frame, reward, done, data = self.step_complete(action)

        return self.frame, reward, done,\
            {"roundDone": data["roundDone"], "stageDone": data["stageDone"],
             "gameDone": data["gameDone"], "epDone": data["epDone"]}

# DIAMBRA Gym base class for two players mode


class DiambraGymHardCore2P(DiambraGymHardCoreBase):
    def __init__(self, env_settings):
        super().__init__(env_settings)

        # Define action spaces, they must be gym.spaces objects
        action_space_dict = {}
        for idx in range(2):
            if self.actionSpace[idx] == "multiDiscrete":
                action_space_dict["P{}".format(idx+1)] =\
                    spaces.MultiDiscrete(self.nActions[idx])
            else:
                action_space_dict["P{}".format(idx+1)] =\
                    spaces.Discrete(
                        self.nActions[idx][0] + self.nActions[idx][1] - 1)

        self.action_space = spaces.Dict(action_space_dict)

    # Step the environment
    def step_complete(self, action):
        # Actions initialization
        mov_act_p1 = 0
        att_act_p1 = 0
        mov_act_p2 = 0
        att_act_p2 = 0

        # Defining move and attack actions P1/P2 as a function of actionSpace
        if self.actionSpace[0] == "multiDiscrete":
            # P1
            mov_act_p1 = action[0]
            att_act_p1 = action[1]
            # P2
            # P2 MultiDiscrete Action Space
            if self.actionSpace[1] == "multiDiscrete":
                mov_act_p2 = action[2]
                att_act_p2 = action[3]
            else:  # P2 Discrete Action Space
                mov_act_p2, att_act_p2 = discrete_to_multi_discrete_action(
                    action[2], self.nActions[1][0])

        else:  # P1 Discrete Action Space
            # P2
            # P2 MultiDiscrete Action Space
            if self.actionSpace[1] == "multiDiscrete":
                # P1
                # Discrete to multidiscrete conversion
                mov_act_p1, att_act_p1 = discrete_to_multi_discrete_action(
                    action[0], self.nActions[0][0])
                mov_act_p2 = action[1]
                att_act_p2 = action[2]
            else:  # P2 Discrete Action Space
                # P1
                # Discrete to multidiscrete conversion
                mov_act_p1, att_act_p1 = discrete_to_multi_discrete_action(
                    action[0], self.nActions[0][0])
                mov_act_p2, att_act_p2 = discrete_to_multi_discrete_action(
                    action[1], self.nActions[1][0])

        self.frame, data = self.arena_engine.step_2p(
            mov_act_p1, att_act_p1, mov_act_p2, att_act_p2)
        reward = data["reward"]
        done = data["gameDone"]
        # data["epDone"]   = done

        return self.frame, reward, done, data

    # Step the environment
    def step(self, action):

        self.frame, reward, done, data = self.step_complete(action)

        return self.frame, reward, done,\
            {"roundDone": data["roundDone"], "stageDone": data["stageDone"],
             "gameDone": data["gameDone"], "epDone": data["epDone"]}

# DIAMBRA Gym base class providing frame and additional info as observations


class DiambraGym1P(DiambraGymHardCore1P):
    def __init__(self, env_settings):
        super().__init__(env_settings)

        # Dictionary observation space
        observation_space_dict = {}
        observation_space_dict['frame'] = spaces.Box(low=0, high=255,
                                                     shape=(self.hwcDim[0],
                                                            self.hwcDim[1],
                                                            self.hwcDim[2]),
                                                     dtype=np.uint8)
        player_spec_dict = {}

        # Adding env additional observations (side-specific)
        for k, v in self.addObs.items():

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
            "move": spaces.Discrete(self.nActions[0][0]),
            "attack": spaces.Discrete(self.nActions[0][1])
        }

        player_spec_dict["actions"] = spaces.Dict(actions_dict)
        observation_space_dict["P1"] = spaces.Dict(player_spec_dict)
        observation_space_dict["stage"] = spaces.Box(low=self.addObs["stage"][1],
                                                     high=self.addObs["stage"][2],
                                                     shape=(), dtype=np.int8)

        self.observation_space = spaces.Dict(observation_space_dict)

    def add_obs_integration(self, frame, data):

        observation = {}
        observation["frame"] = frame
        observation["stage"] = data["stage"]

        player_spec_dict = {}

        # Adding env additional observations (side-specific)
        for k, v in self.addObs.items():

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
            {"roundDone": data["roundDone"], "stageDone": data["stageDone"],
             "gameDone": data["gameDone"], "epDone": data["epDone"]}

    # Reset the environment
    def reset(self):
        self.frame, data, self.player_side = self.arena_engine.reset()
        observation = self.add_obs_integration(self.frame, data)
        return observation

# DIAMBRA Gym base class providing frame and additional info as observations


class DiambraGym2P(DiambraGymHardCore2P):
    def __init__(self, env_settings):
        super().__init__(env_settings)

        # Dictionary observation space
        observation_space_dict = {}
        observation_space_dict['frame'] = spaces.Box(low=0, high=255,
                                                     shape=(self.hwcDim[0],
                                                            self.hwcDim[1],
                                                            self.hwcDim[2]),
                                                     dtype=np.uint8)
        player_spec_dict = {}

        # Adding env additional observations (side-specific)
        for k, v in self.addObs.items():

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
            "move": spaces.Discrete(self.nActions[0][0]),
            "attack": spaces.Discrete(self.nActions[0][1])
        }

        player_spec_dict["actions"] = spaces.Dict(actions_dict)
        player_dict_p1 = player_spec_dict.copy()
        observation_space_dict["P1"] = spaces.Dict(player_dict_p1)

        actions_dict = {
            "move": spaces.Discrete(self.nActions[1][0]),
            "attack": spaces.Discrete(self.nActions[1][1])
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
            for k, v in self.addObs.items():

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
            {"roundDone": data["roundDone"], "stageDone": data["stageDone"],
             "gameDone": data["gameDone"], "epDone": data["epDone"]}

    # Reset the environment
    def reset(self):
        self.frame, data, self.player_side = self.arena_engine.reset()
        observation = self.add_obs_integration(self.frame, data)
        return observation


def make_gym_env(env_settings):

    if env_settings["player"] != "P1P2":  # 1P Mode
        if env_settings["hardCore"]:
            env = DiambraGymHardCore1P(env_settings)
        else:
            env = DiambraGym1P(env_settings)
    else:  # 2P Mode
        if env_settings["hardCore"]:
            env = DiambraGymHardCore2P(env_settings)
        else:
            env = DiambraGym2P(env_settings)

    return env, env_settings["player"]
