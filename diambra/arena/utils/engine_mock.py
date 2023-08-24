import time
import random
import numpy as np
import diambra.arena
from diambra.engine import model

class DiambraEngineMock:

    def __init__(self, fps=1000):

        # Game features
        self.game_data = None
        self.fps = fps

        # Class state variables initialization
        self.timer = 0
        self.n_rounds_won = 0
        self.n_rounds_lost = 0
        self.current_stage_number = 1
        self.n_continue = 0
        self.side = {"P1": 0, "P2": 1}
        self.char = {"P1": 0, "P2": 0}
        self.health = {"P1": 0, "P2": 0}
        self.player = ""
        self.perfect = False

    def _generate_ram_states(self):

        for k, v in self.ram_states.items():
            self.ram_states[k][3] = random.choice(range(v[1], v[2] + 1))

        # Setting meaningful values to ram states
        self.ram_states["stage"][3] = self.current_stage_number
        self.ram_states["sideP1"][3] = self.side["P1"]
        self.ram_states["sideP2"][3] = self.side["P2"]
        self.ram_states["winsP1"][3] = self.n_rounds_won
        self.ram_states["winsP2"][3] = self.n_rounds_lost

        values = [self.char, self.health]

        for idx, state in enumerate(["char", "health"]):
            for text in ["", "_1", "_2", "_3"]:
                for player in ["P1", "P2"]:
                    key = "{}{}{}".format(state, text, player)
                    if (key in self.ram_states):
                        self.ram_states[key][3] = values[idx][player]

        self.ram_states["timer"][3] = int(self.timer)

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
        self.n_rounds_won = 0
        self.n_rounds_lost = 0
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

        self.side["P1"] = 0 if self.settings.variable_env_settings.player_env_settings[0].role == "P1" else 1
        self.side["P2"] = 1 if self.settings.variable_env_settings.player_env_settings[0].role == "P1" else 0
        self.health["P1"] = self.game_data["health"][1]
        self.health["P2"] = self.game_data["health"][1]
        self.timer = self.game_data["ram_states"]["timer"][2]

        self.reward = 0

        # Characters
        for idx in range(self.settings.n_players):
            self.char[self.settings.variable_env_settings.player_env_settings[idx].role] =\
                self.game_data["char_list"].index(self.settings.variable_env_settings.player_env_settings[idx].characters[0])

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
            "P1": self.health["P1"],
            "P2": self.health["P2"]
        }

        # Health evolution
        hit_prob = self.base_round_winning_probability ** self.current_stage_number

        for idx in range(self.settings.n_players):
            role = self.settings.variable_env_settings.player_env_settings[idx].role
            opponent_role = "P2" if role == "P1" else "P1"
            if self.player_actions[idx][1] != 0:
                self.health[opponent_role] -= random.choices([self.base_hit, 0], [hit_prob, 1.0 - hit_prob])[0]
            if not self.perfect:
                self.health[role] -= random.choices([self.base_hit, 0], [1.0 - hit_prob, hit_prob])[0]

        for role in ["P1", "P2"]:
            self.health[role] = max(self.health[role], self.game_data["health"][0])

        role_0 = self.settings.variable_env_settings.player_env_settings[0].role
        opponent_role_0 = "P2" if role_0 == "P1" else "P1"

        if (min(self.health["P1"], self.health["P2"]) == self.game_data["health"][0]) or (self.timer <= 0):
            self.round_done_ = True

            if self.health[role_0] > self.health[opponent_role_0]:
                self.health[opponent_role_0] = self.game_data["health"][0]
                print("Round won")
                self.n_rounds_won += 1
            elif self.health[role_0] < self.health[opponent_role_0]:
                self.health[role_0] = self.game_data["health"][0]
                print("Round lost")
                self.n_rounds_lost += 1
            else:
                print("Draw, forcing lost")
                self.n_rounds_lost += 1
                self.health[role_0] = self.game_data["health"][0]

        if self.n_rounds_won == self.game_data["rounds_per_stage"]:
            self.stage_done_ = True
            self.current_stage_number += 1
            self.n_rounds_won = 0
            self.n_rounds_lost = 0
            if self.settings.n_players == 2:
                self.game_done_ = True
                self.episode_done_ = True
            else:
                self.char[opponent_role_0] = self.current_stage_number
            print("Stage done")
            print("Moving to stage {} of {}".format(self.current_stage_number, self.game_data["stages_per_game"]))

        if self.n_rounds_lost == self.game_data["rounds_per_stage"]:
            print("Game done")
            self.game_done_ = True
            if self.n_continue >= self.continue_per_episode:
                print("Episode done")
                self.episode_done_ = True
            else:
                print("Continuing game")
                self.n_continue += 1
                self.n_rounds_won = 0
                self.n_rounds_lost = 0

        if self.current_stage_number == self.game_data["stages_per_game"]:
            print("Episode done")
            print("Game completed!")
            self.game_done_ = True
            self.episode_done_ = True

        self.env_done_ = self.episode_done_

        delta = {
            "P1": starting_health["P1"] - self.health["P1"],
            "P2": starting_health["P2"] - self.health["P2"]
        }
        self.reward = delta[opponent_role_0] - delta[role_0]

        if np.any([self.round_done_, self.stage_done_, self.game_done_]):
            self.side["P1"] = 0
            self.side["P2"] = 1
            self.health["P1"] = self.game_data["health"][1]
            self.health["P2"] = self.game_data["health"][1]
            self.timer = self.game_data["ram_states"]["timer"][2]

            # Set perfect chance
            self._set_perfect_chance()
        else:
            self.side["P1"] = random.choices([0, 1], [0.3, 0.7])[0]
            self.side["P2"] = random.choices([(self.side["P1"] + 1) % 2, self.side["P1"]], [0.97, 0.03])[0]

    def _update_step_reset_response(self):

        # Response
        response = model.StepResetResponse()

        # Ram states
        self._generate_ram_states()
        for k, v in self.ram_states.items():
            response.observation.ram_states[k] = v[3]

        # Game state
        response.info.game_states["round_done"] = self.round_done_
        response.info.game_states["stage_done"] = self.stage_done_
        response.info.game_states["game_done"] = self.game_done_
        response.info.game_states["episode_done"] = self.episode_done_
        response.info.game_states["env_done"] = self.env_done_

        # Frame
        response.observation.frame = self._generate_frame()

        # Reward
        response.reward = self.reward

        return response

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

        difficulty = self.settings.variable_env_settings.difficulty
        if difficulty == 0:
            difficulty = random.choice(range(self.game_data["difficulty"][0], self.game_data["difficulty"][1] + 1))
        difficulty_level = self.game_data["difficulty_to_cluster_map"][str(difficulty)]

        self.base_round_winning_probability = probability_maps[difficulty_level][0] ** (1.0/self.game_data["stages_per_game"])
        self.perfect_probability = probability_maps[difficulty_level][1]

        self.frame_shape = self.game_data["frame_shape"]
        if (self.settings.frame_shape.h > 0 and self.settings.frame_shape.w > 0):
            self.frame_shape[0] = self.settings.frame_shape.h
            self.frame_shape[1] = self.settings.frame_shape.w
        if (self.settings.frame_shape.c == 1):
            self.frame_shape[2] = self.settings.frame_shape.c

        continue_game_setting = self.settings.variable_env_settings.continue_game
        self.continue_per_episode = - int(continue_game_setting) if continue_game_setting < 0.0 else int(continue_game_setting*10)
        self.delta_health = self.game_data["health"][1] - self.game_data["health"][0]
        self.base_hit = int(self.delta_health * self.game_data["n_actions"][1] /
                              ((self.game_data["n_actions"][0] + self.game_data["n_actions"][1]) *
                               (self.game_data["ram_states"]["timer"][2] / self.settings.step_ratio)))

        # Generate the ram states map
        self.ram_states = self.game_data["ram_states"]
        for k, v in self.ram_states.items():
                self.ram_states[k].append(0)

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

        # Difficulty bounds
        response.difficulty_bounds.min = self.game_data["difficulty"][0]
        response.difficulty_bounds.max = self.game_data["difficulty"][1]

        # RAM states
        self._generate_ram_states()
        for k, v in self.ram_states.items():
            response.ram_states[k].type = v[0]
            response.ram_states[k].min = v[1]
            response.ram_states[k].max = v[2]

        return response

    # Reset the environment [pb low level]
    def mock_reset(self, variable_env_settings):
        # Update variable env settings
        self.settings.variable_env_settings.CopyFrom(variable_env_settings)

        # Random seed
        random.seed(self.settings.variable_env_settings.random_seed)
        np.random.seed(self.settings.variable_env_settings.random_seed)

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
