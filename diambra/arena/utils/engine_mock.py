import time
import random
import numpy as np
import diambra.arena
from copy import deepcopy
from diambra.engine import model
from diambra.arena import Roles

class DiambraEngineMock:
    def __init__(self, fps=1000, override_perfect_probability=None):

        # Game features
        self.game_data = None
        self.fps = fps

        # Class state variables initialization
        self.timer = 0
        self.current_stage_number = 1
        self.n_continue = 0
        self.side = {Roles.P1: 0, Roles.P2: 1}
        self.char = {Roles.P1: 0, Roles.P2: 0}
        self.health = {Roles.P1: 0, Roles.P2: 0}
        self.wins = {Roles.P1: 0, Roles.P2: 0}
        self.player = ""
        self.perfect = False
        self.override_perfect_probability = override_perfect_probability

    def mock__init__(self, env_address, grpc_timeout=60):
        print("Trying to connect to DIAMBRA Engine server (timeout={}s)...".format(grpc_timeout))
        print("... done (MOCKED!).")

    # Send env settings, retrieve env info and int variables list [pb low level]
    def mock_env_init(self, env_settings_pb):
        self.settings = env_settings_pb

        # Print settings
        print("Settings:")
        print(self.settings)

        # Retrieve game info
        self.game_data = diambra.arena.available_games(print_out=False)[self.settings.game_id]

        # Setting win and perfect probability based on game difficulty
        probability_maps = {
            "Easy": [0.75, 0.4],
            "Medium": [0.5, 0.2],
            "Hard": [0.25, 0.1],
        }

        difficulty = self.settings.episode_settings.difficulty
        if difficulty == 0:
            difficulty = random.choice(range(self.game_data["difficulty"][0], self.game_data["difficulty"][1] + 1))
        difficulty_level = self.game_data["difficulty_to_cluster_map"][str(difficulty)]

        self.base_round_winning_probability = probability_maps[difficulty_level][0] ** (1.0/self.game_data["stages_per_game"])
        self.perfect_probability = probability_maps[difficulty_level][1]
        if self.override_perfect_probability is not None:
            self.perfect_probability = self.override_perfect_probability

        self.frame_shape = self.game_data["frame_shape"]
        if (self.settings.frame_shape.h > 0 and self.settings.frame_shape.w > 0):
            self.frame_shape[0] = self.settings.frame_shape.h
            self.frame_shape[1] = self.settings.frame_shape.w
        if (self.settings.frame_shape.c == 1):
            self.frame_shape[2] = self.settings.frame_shape.c

        continue_game_setting = self.settings.episode_settings.continue_game
        self.continue_per_episode = - int(continue_game_setting) if continue_game_setting < 0.0 else int(continue_game_setting*10)
        self.delta_health = self.game_data["health"][1] - self.game_data["health"][0]
        self.base_hit = int(self.delta_health * self.game_data["n_actions"][1] /
                              ((self.game_data["n_actions"][0] + self.game_data["n_actions"][1]) *
                               (self.game_data["ram_states"]["common"]["timer"][2] / self.settings.step_ratio)))

        # Generate the ram states map
        self.ram_states = {}
        self.ram_states[model.RamStatesCategories.common] = self.game_data["ram_states"]["common"]
        self.ram_states[model.RamStatesCategories.P1] = deepcopy(self.game_data["ram_states"]["Px"])
        self.ram_states[model.RamStatesCategories.P2] = deepcopy(self.game_data["ram_states"]["Px"])
        for k, v in self.ram_states.items():
            for k2, v2 in v.items():
                self.ram_states[k][k2].append(0)

        # Build the response
        response = model.EnvInitResponse()

        # Frame
        response.frame_shape.h = self.frame_shape[0]
        response.frame_shape.w = self.frame_shape[1]
        response.frame_shape.c = self.frame_shape[2]

        # Available actions
        response.available_actions.n_moves = self.game_data["n_actions"][0]
        response.available_actions.n_attacks = self.game_data["n_actions"][1]
        response.available_actions.n_attacks_no_comb = self.game_data["n_actions"][2]

        move_keys = ["NoMove", "Left", "UpLeft", "Up", "UpRight", "Right", "DownRight", "Down", "DownLeft"]
        move_labels = [" ", "\u2190", "\u2196", "\u2191", "\u2197", "\u2192", "\u2198", "\u2193", "\u2199"]
        for idx in range(self.game_data["n_actions"][0]):
            button = model.EnvInitResponse.AvailableActions.Button()
            button.key = move_keys[idx]
            button.label = move_labels[idx]
            response.available_actions.moves.append(button)

        attack_keys = ["But{}".format(i) for i in range(self.game_data["n_actions"][2])] +\
                      ["But{}But{}".format(i - self.game_data["n_actions"][2] + 1, i - self.game_data["n_actions"][2] + 2)\
                          for i in range(self.game_data["n_actions"][2], self.game_data["n_actions"][1])]
        attack_labels = [" "]
        for i in range(1, self.game_data["n_actions"][1]):
            attack_labels += ["Attack{}".format(i)]
        for idx in range(self.game_data["n_actions"][1]):
            button = model.EnvInitResponse.AvailableActions.Button()
            button.key = attack_keys[idx]
            button.label = attack_labels[idx]
            response.available_actions.attacks.append(button)

        # Cumulative reward bounds
        response.cumulative_reward_bounds.min = -((self.game_data["rounds_per_stage"] - 1) * (self.game_data["stages_per_game"] - 1) + self.game_data["rounds_per_stage"]) * self.delta_health
        response.cumulative_reward_bounds.max = self.game_data["rounds_per_stage"] * self.game_data["stages_per_game"] * self.delta_health

        # Characters info
        response.characters_info.char_list.extend(self.game_data["char_list"])
        response.characters_info.char_forbidden_list.extend(self.game_data["char_forbidden_list"])
        for key, value in self.game_data["char_homonymy_map"].items():
            response.characters_info.char_homonymy_map[key] = value
        response.characters_info.chars_per_round = self.game_data["number_of_chars_per_round"]
        response.characters_info.chars_to_select = self.game_data["number_of_chars_to_select"]

        # Difficulty bounds
        response.difficulty_bounds.min = self.game_data["difficulty"][0]
        response.difficulty_bounds.max = self.game_data["difficulty"][1]

        # RAM states
        self._generate_ram_states()
        for k, v in self.ram_states.items():
            for k2, v2 in v.items():
                k2_enum =model.RamStates.Value(k2)
                response.ram_states_categories[k].ram_states[k2_enum].type = model.SpaceTypes.Value(v2[0])
                response.ram_states_categories[k].ram_states[k2_enum].min = v2[1]
                response.ram_states_categories[k].ram_states[k2_enum].max = v2[2]

        return response

    # Reset the environment [pb low level]
    def mock_reset(self, episode_settings):
        # Update variable env settings
        self.settings.episode_settings.CopyFrom(episode_settings)

        # Random seed
        random.seed(self.settings.episode_settings.random_seed)
        np.random.seed(self.settings.episode_settings.random_seed)

        self._reset_state()

        return self._update_step_reset_response()

    # Step the environment [pb low level]
    def mock_step(self, actions):
        # Update class state
        self._new_game_state(actions)

        return self._update_step_reset_response()

    # Closing DIAMBRA Arena
    def mock_close(self):
        pass

    def _generate_ram_states(self):
        for k, v in self.ram_states.items():
            for k2, v2 in v.items():
                self.ram_states[k][k2][3] = random.choice(range(v2[1], v2[2] + 1))

        # Setting meaningful values to ram states
        values = [self.char, self.health, self.wins, self.side]

        for idx, state in enumerate(["character", "health", "wins", "side"]):
            for text in ["", "_1", "_2", "_3"]:
                for player in [Roles.P1, Roles.P2]:
                    key = "{}{}".format(state, text)
                    if (key in self.ram_states[player]):
                        self.ram_states[player][key][3] = values[idx][player]

        self.ram_states[model.RamStatesCategories.common]["stage"][3] = int(self.current_stage_number)
        self.ram_states[model.RamStatesCategories.common]["timer"][3] = int(self.timer)

    def _generate_frame(self):
        frame = np.ones((self.frame_shape), dtype=np.int8) * ((self.current_stage_number * self.game_data["rounds_per_stage"] + int(self.timer)) % 255)
        return frame.tobytes()

    # Set delta health
    def _set_perfect_chance(self):
        self.perfect = random.choices([True, False], [self.perfect_probability, 1.0 - self.perfect_probability])[0]
        # Force perfect to true in case of 2P games to avoid double update for own role (see health evolution in new_game_state)
        self.perfect = self.perfect or self.settings.n_players == 2

    # Reset game state
    def _reset_state(self):
        # Reset class state
        self.current_stage_number = 1
        self.n_continue = 0

        # Actions
        self.player_actions = [[0, 0], [0, 0]]

        # Set perfect chance
        self._set_perfect_chance()

        # Done flags
        self.round_done_ = False
        self.stage_done_ = False
        self.game_done_ = False
        self.episode_done_ = False
        self.env_done_ = False

        self.side[Roles.P1] = 0
        self.side[Roles.P2] = 1
        self.health[Roles.P1] = self.game_data["health"][1]
        self.health[Roles.P2] = self.game_data["health"][1]
        self.wins[Roles.P1] = 0
        self.wins[Roles.P2] = 0
        self.timer = self.game_data["ram_states"]["common"]["timer"][2]

        self.reward = 0

        # Characters
        for idx in range(self.settings.n_players):
            self.char[self.settings.episode_settings.player_settings[idx].role] =\
                self.game_data["char_list"].index(self.settings.episode_settings.player_settings[idx].characters[0])

    # Update game state
    def _new_game_state(self, actions):
        # Sleep to simulate computer time elapsed
        time.sleep(1.0/(self.settings.step_ratio * self.fps))

        # Actions
        for idx, action in enumerate(actions):
            self.player_actions[idx] = [action[0], action[1]]

        # Done flags
        self.round_done_ = False
        self.stage_done_ = False
        self.game_done_ = False
        self.episode_done_ = False
        self.env_done_ = False

        self.timer -= (1.0 * self.settings.step_ratio) / 60.0

        starting_health = {
            Roles.P1: self.health[Roles.P1],
            Roles.P2: self.health[Roles.P2]
        }

        # Health evolution
        hit_prob = self.base_round_winning_probability ** self.current_stage_number

        for idx in range(self.settings.n_players):
            role = self.settings.episode_settings.player_settings[idx].role
            opponent_role = Roles.P2 if role == Roles.P1 else Roles.P1
            if self.player_actions[idx][1] != 0:
                self.health[opponent_role] -= random.choices([self.base_hit, 0], [hit_prob, 1.0 - hit_prob])[0]
            if not self.perfect:
                self.health[role] -= random.choices([self.base_hit, 0], [1.0 - hit_prob, hit_prob])[0]

        for role in [Roles.P1, Roles.P2]:
            self.health[role] = max(self.health[role], self.game_data["health"][0])

        role_0 = self.settings.episode_settings.player_settings[0].role
        opponent_role_0 = Roles.P2 if role_0 == Roles.P1 else Roles.P1

        if (min(self.health[Roles.P1], self.health[Roles.P2]) == self.game_data["health"][0]) or (self.timer <= 0):
            self.round_done_ = True

            if self.health[role_0] > self.health[opponent_role_0]:
                self.health[opponent_role_0] = self.game_data["health"][0]
                print("Round won")
                self.wins[role_0] += 1
            elif self.health[role_0] < self.health[opponent_role_0]:
                self.health[role_0] = self.game_data["health"][0]
                print("Round lost")
                self.wins[opponent_role_0] += 1
            else:
                print("Draw, forcing lost")
                self.wins[opponent_role_0] += 1
                self.health[role_0] = self.game_data["health"][0]

        if self.wins[role_0] == self.game_data["rounds_per_stage"]:
            self.stage_done_ = True
            self.current_stage_number += 1
            self.wins[role_0] = 0
            self.wins[opponent_role_0] = 0
            if self.settings.n_players == 2:
                self.game_done_ = True
                self.episode_done_ = True
            else:
                self.char[opponent_role_0] = self.current_stage_number
            print("Stage done")
            print("Moving to stage {} of {}".format(self.current_stage_number, self.game_data["stages_per_game"]))

        if self.wins[opponent_role_0] == self.game_data["rounds_per_stage"]:
            print("Game done")
            self.game_done_ = True
            if self.n_continue >= self.continue_per_episode:
                print("Episode done")
                self.episode_done_ = True
            else:
                print("Continuing game")
                self.n_continue += 1
                self.wins[role_0] = 0
                self.wins[opponent_role_0] = 0

        if self.current_stage_number == self.game_data["stages_per_game"]:
            print("Episode done")
            print("Game completed!")
            self.game_done_ = True
            self.episode_done_ = True

        self.env_done_ = self.episode_done_

        delta = {
            Roles.P1: starting_health[Roles.P1] - self.health[Roles.P1],
            Roles.P2: starting_health[Roles.P2] - self.health[Roles.P2]
        }
        self.reward = delta[opponent_role_0] - delta[role_0]

        if np.any([self.round_done_, self.stage_done_, self.game_done_]):
            self.side[Roles.P1] = 0
            self.side[Roles.P2] = 1
            self.health[Roles.P1] = self.game_data["health"][1]
            self.health[Roles.P2] = self.game_data["health"][1]
            self.timer = self.game_data["ram_states"]["common"]["timer"][2]

            # Set perfect chance
            self._set_perfect_chance()
        else:
            self.side[Roles.P1] = random.choices([0, 1], [0.3, 0.7])[0]
            self.side[Roles.P2] = random.choices([(self.side[Roles.P1] + 1) % 2, self.side[Roles.P2]], [0.97, 0.03])[0]

    def _update_step_reset_response(self):

        # Response
        response = model.StepResetResponse()

        # Ram states
        self._generate_ram_states()
        for k, v in self.ram_states.items():
            for k2, v2 in v.items():
                response.observation.ram_states_categories[k].ram_states[model.RamStates.Value(k2)] = v2[3]

        # Game state
        response.info.game_states[model.GameStates.round_done] = self.round_done_
        response.info.game_states[model.GameStates.stage_done] = self.stage_done_
        response.info.game_states[model.GameStates.game_done] = self.game_done_
        response.info.game_states[model.GameStates.episode_done] = self.episode_done_
        response.info.game_states[model.GameStates.env_done] = self.env_done_

        # Frame
        response.observation.frame = self._generate_frame()

        # Reward
        response.reward = self.reward

        return response

def load_mocker(mocker, **kwargs):
    diambra_engine_mock = DiambraEngineMock(**kwargs)

    mocker.patch("diambra.arena.engine.interface.DiambraEngine.__init__", diambra_engine_mock.mock__init__)
    mocker.patch("diambra.arena.engine.interface.DiambraEngine.env_init", diambra_engine_mock.mock_env_init)
    mocker.patch("diambra.arena.engine.interface.DiambraEngine.reset", diambra_engine_mock.mock_reset)
    mocker.patch("diambra.arena.engine.interface.DiambraEngine.step", diambra_engine_mock.mock_step)
    mocker.patch("diambra.arena.engine.interface.DiambraEngine.close", diambra_engine_mock.mock_close)