import time
import random
import numpy as np
import diambra.arena
from diambra.engine import Client, model

class DiambraEngineMock:

    def __init__(self, steps_per_round=20, fps=1000):

        # Game features
        self.game_data = None
        self.steps_per_round = steps_per_round
        self.fps = fps

        # Random seed
        time_dep_seed = int((time.time() - int(time.time() - 0.5)) * 1000)
        random.seed(time_dep_seed)

        # Class state variables initialization
        self.n_steps = 0
        self.n_rounds_won = 0
        self.n_rounds_lost = 0
        self.n_stages = 0
        self.n_continue = 0
        self.side_p1 = 0
        self.side_p2 = 1
        self.char_p1 = 0
        self.char_p2 = 0
        self.health_p1 = 0
        self.health_p2 = 0
        self.player = ""
        self.perfect = False

    def _mock__init__(self, env_address, grpc_timeout=60):
        print("Trying to connect to DIAMBRA Engine server (timeout={}s)...".format(grpc_timeout))
        print("... done (MOCKED!).")

    def generate_ram_states(self):

        for k, v in self.ram_states.items():
            self.ram_states[k][3] = random.choices(range(v[1], v[2] + 1))[0]

        # Setting meaningful values to ram states
        self.ram_states["stage"][3] = self.n_stages + 1
        self.ram_states["SideP1"][3] = self.side_p1
        self.ram_states["SideP2"][3] = self.side_p2
        self.ram_states["WinsP1"][3] = self.n_rounds_won
        self.ram_states["WinsP2"][3] = self.n_rounds_lost

        self.ram_states["CharP1"][3] = self.char_p1
        self.ram_states["CharP2"][3] = self.char_p2

        if self.game_data["number_of_chars_per_round"] == 1:
            self.ram_states["HealthP1"][3] = self.health_p1
            self.ram_states["HealthP2"][3] = self.health_p2
        else:
            for idx in range(self.game_data["number_of_chars_per_round"]):
                self.ram_states["Health{}P1".format(idx+1)][3] = self.health_p1
                self.ram_states["Health{}P2".format(idx+1)][3] = self.health_p2

    # Send env settings, retrieve env info and int variables list [pb low level]
    def _mock_env_init(self, env_settings_pb):
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

        difficulty_level = self.game_data["difficulty_to_cluster_map"][str(self.settings.difficulty)]

        self.base_round_winning_probability = probability_maps[difficulty_level][0] ** (1.0/self.game_data["stages_per_game"])
        self.perfect_probability = probability_maps[difficulty_level][1]

        self.frame_shape = self.game_data["frame_shape"]
        if (self.settings.frame_shape.h > 0 and self.settings.frame_shape.w > 0):
            self.frame_shape[0] = self.settings.frame_shape.h
            self.frame_shape[1] = self.settings.frame_shape.w
        if (self.settings.frame_shape.c == 1):
            self.frame_shape[2] = self.settings.frame_shape.c

        self.continue_per_episode = - int(self.settings.continue_game) if self.settings.continue_game < 0.0 else int(self.settings.continue_game*10)
        self.delta_health = self.game_data["health"][1] - self.game_data["health"][0]
        self.base_hit = int(self.delta_health * (self.game_data["n_actions"][0] + self.game_data["n_actions"][0]) / (self.game_data["n_actions"][1] * (self.steps_per_round - 1)))

        # Generate the ram states map
        self.ram_states = self.game_data["ram_states"]
        for k, v in self.ram_states.items():
                self.ram_states[k].append(0)

        # Build the response
        response = model.EnvInitResponse()

        response.frame_shape.h = self.frame_shape[0]
        response.frame_shape.w = self.frame_shape[1]
        response.frame_shape.c = self.frame_shape[2]

        response.available_actions.with_buttons_combination.moves = self.game_data["n_actions"][0]
        response.available_actions.with_buttons_combination.attacks = self.game_data["n_actions"][2]
        response.available_actions.without_buttons_combination.moves = self.game_data["n_actions"][0]
        response.available_actions.without_buttons_combination.attacks = self.game_data["n_actions"][1]

        response.delta_health = self.delta_health
        response.max_stage = self.game_data["stages_per_game"]
        response.cumulative_reward_bounds.min = -((self.game_data["rounds_per_stage"] - 1) * (response.max_stage - 1) + self.game_data["rounds_per_stage"]) * response.delta_health
        response.cumulative_reward_bounds.max = self.game_data["rounds_per_stage"] * response.max_stage * response.delta_health
        response.char_list.extend(self.game_data["char_list"])

        response.buttons.moves.extend(["NoMove", "Left", "UpLeft", "Up", "UpRight", "Right", "DownRight", "Down", "DownLeft"])
        response.buttons.attacks.extend(["But{}".format(i) for i in range(self.game_data["n_actions"][1])] +\
                                        ["But{}But{}".format(i - self.game_data["n_actions"][1] + 1, i - self.game_data["n_actions"][1] + 2)\
                                        for i in range(self.game_data["n_actions"][1], self.game_data["n_actions"][2])])
        response.button_mapping.moves.extend(["0", " ", "1", "\u2190", "2", "\u2196", "3", "\u2191",
                                              "4", "\u2197", "5", "\u2192", "6", "\u2198", "7", "\u2193", "8", "\u2199"])
        attack_mapping = ["0", " "]
        for i in range(1, self.game_data["n_actions"][2]):
            attack_mapping += [str(i), "Attack{}".format(i)]
        response.button_mapping.attacks.extend(attack_mapping)

        self.generate_ram_states()
        for k, v in self.ram_states.items():
            response.ram_states[k].type = v[0]
            response.ram_states[k].min = v[1]
            response.ram_states[k].max = v[2]
            response.ram_states[k].val = v[3]

        return response

    def generate_frame(self):
        frame = np.ones((self.frame_shape), dtype=np.int8) * ((self.n_stages * self.game_data["rounds_per_stage"] + self.n_steps) % 255)
        return frame.tobytes()

    # Set delta health
    def set_perfect_chance(self):
        self.perfect = random.choices([True, False], [self.perfect_probability, 1.0 - self.perfect_probability])[0]

    # Reset game state
    def reset_state(self):
        # Reset class state
        self.n_steps = 0
        self.n_rounds_won = 0
        self.n_rounds_lost = 0
        self.n_stages = 0
        self.n_continue = 0

        # Actions
        self.mov_p1 = 0
        self.att_p1 = 0
        self.mov_p2 = 0
        self.att_p2 = 0

        # Player
        if self.settings.player != "Random":
            self.player = self.settings.player
        else:
            self.player = random.choices(["P1", "P2"])[0]

        # Set delta healths
        self.set_perfect_chance()

        # Done flags
        self.round_done_ = False
        self.stage_done_ = False
        self.game_done_ = False
        self.episode_done_ = False
        self.env_done_ = False

        self.side_p1 = 0
        self.side_p2 = 1
        self.health_p1 = self.game_data["health"][1]
        self.health_p2 = self.game_data["health"][1]

        self.reward = 0

        # Characters
        if self.player == "P1P2":
            if (self.settings.characters.p1[0] == "Random"):
                self.char_p1 = random.choices(range(len(self.game_data["char_list"])))[0]
            else:
                self.char_p1 = self.game_data["char_list"].index(self.settings.characters.p1[0])

            if (self.settings.characters.p2[0] == "Random"):
                self.char_p2 = random.choices(range(len(self.game_data["char_list"])))[0]
            else:
                self.char_p2 = self.game_data["char_list"].index(self.settings.characters.p2[0])

        elif self.player == "P1":
            self.char_p2 = self.n_stages
            if (self.settings.characters.p1[0] == "Random"):
                self.char_p1 = random.choices(range(len(self.game_data["char_list"])))[0]
            else:
                self.char_p1 = self.game_data["char_list"].index(self.settings.characters.p1[0])

        else:
            self.char_p1 = self.n_stages
            if (self.settings.characters.p2[0] == "Random"):
                self.char_p2 = random.choices(range(len(self.game_data["char_list"])))[0]
            else:
                self.char_p2 = self.game_data["char_list"].index(self.settings.characters.p2[0])

    # Update game state
    def new_game_state(self, mov_p1=0, att_p1=0, mov_p2=0, att_p2=0):

        # Sleep to simulate computer time elapsed
        time.sleep(1.0/self.fps)

        # Actions
        self.mov_p1 = mov_p1
        self.att_p1 = att_p1
        self.mov_p2 = mov_p2
        self.att_p2 = att_p2

        # Done flags
        self.round_done_ = False
        self.stage_done_ = False
        self.game_done_ = False
        self.episode_done_ = False
        self.env_done_ = False

        self.n_steps += 1

        starting_health_p1 = self.health_p1
        starting_health_p2 = self.health_p2

        # Health evolution
        hit_prob = self.base_round_winning_probability ** self.n_stages

        if self.player == "P2":
            if not self.perfect:
                self.health_p2 -= random.choices([self.base_hit, 0], [1.0 - hit_prob, hit_prob])[0]
            if att_p1 != 0:
                self.health_p1 -= random.choices([self.base_hit, 0], [hit_prob, 1.0 - hit_prob])[0]
        else:
            self.health_p1 -= random.choices([self.base_hit, 0], [1.0 - hit_prob, hit_prob])[0]
            if att_p1 != 0:
                self.health_p2 -= random.choices([self.base_hit, 0], [hit_prob, 1.0 - hit_prob])[0]
            if (self.player == "P1P2" and att_p2 == 0) or self.perfect:
                self.health_p1 = starting_health_p1

        self.health_p1 = max(self.health_p1, self.game_data["health"][0])
        self.health_p2 = max(self.health_p2, self.game_data["health"][0])

        if (min(self.health_p1, self.health_p2) == self.game_data["health"][0]) or ((self.n_steps % self.steps_per_round) == 0):
            self.round_done_ = True

            if self.health_p1 > self.health_p2:
                self.health_p2 = self.game_data["health"][0]
                if self.player == "P2":
                    print("Round lost")
                    self.n_rounds_lost += 1
                else:
                    print("Round won")
                    self.n_rounds_won += 1

            elif self.health_p2 > self.health_p1:
                self.health_p1 = self.game_data["health"][0]
                if self.player == "P2":
                    print("Round won")
                    self.n_rounds_won += 1
                else:
                    print("Round lost")
                    self.n_rounds_lost += 1
            else:
                print("Draw, forcing lost")
                self.n_rounds_lost += 1
                if self.player == "P2":
                    self.health_p2 = self.game_data["health"][0]
                else:
                    self.health_p1 = self.game_data["health"][0]

        if self.n_rounds_won == self.game_data["rounds_per_stage"]:
            self.stage_done_ = True
            self.n_stages += 1
            self.n_rounds_won = 0
            self.n_rounds_lost = 0
            if self.player == "P1P2":
                self.game_done_ = True
                self.episode_done_ = True
            elif self.player == "P1":
                self.char_p2 = self.n_stages
            else:
                self.char_p1 = self.n_stages

        if self.n_rounds_lost == self.game_data["rounds_per_stage"]:
            self.game_done_ = True
            if self.n_continue >= self.continue_per_episode:
                self.episode_done_ = True
            else:
                self.n_continue += 1
                self.n_rounds_won = 0
                self.n_rounds_lost = 0

        if self.n_stages == self.game_data["stages_per_game"]:
            self.game_done_ = True
            self.episode_done_ = True

        self.env_done_ = self.episode_done_

        delta_p1 = starting_health_p1 - self.health_p1
        delta_p2 = starting_health_p2 - self.health_p2
        self.reward = delta_p1 - delta_p2 if self.player == "P2" else delta_p2 - delta_p1

        if np.any([self.round_done_, self.stage_done_, self.game_done_]):

            self.n_steps = 0

            self.side_p1 = 0
            self.side_p2 = 1
            self.health_p1 = self.game_data["health"][1]
            self.health_p2 = self.game_data["health"][1]

            # Set delta healths
            self.set_perfect_chance()
        else:
            self.side_p1 = random.choices([0, 1], [0.3, 0.7])[0]
            self.side_p2 = random.choices([(self.side_p1 + 1) % 2, self.side_p1], [0.97, 0.03])[0]

    def update_observation(self):

        # Response
        observation = model.Observation()

        # Actions
        observation.actions.p1.move = self.mov_p1
        observation.actions.p1.attack = self.att_p1
        observation.actions.p2.move = self.mov_p2
        observation.actions.p2.attack = self.att_p2

        # Ram states
        self.generate_ram_states()
        for k, v in self.ram_states.items():
            observation.ram_states[k].type = v[0]
            observation.ram_states[k].min = v[1]
            observation.ram_states[k].max = v[2]
            observation.ram_states[k].val = v[3]

        # Game state
        observation.game_state.round_done = self.round_done_
        observation.game_state.stage_done = self.stage_done_
        observation.game_state.game_done = self.game_done_
        observation.game_state.episode_done = self.episode_done_
        observation.game_state.env_done = self.env_done_

        # Player
        observation.player = self.player

        # Frame
        observation.frame = self.generate_frame()

        # Reward
        observation.reward = self.reward

        return observation


    # Reset the environment [pb low level]
    def _mock_reset(self):

        self.reset_state()

        return self.update_observation()

    # Step the environment (1P) [pb low level]
    def _mock_step_1p(self, mov_p1, att_p1):

        # Update class state
        self.new_game_state(mov_p1, att_p1)

        return self.update_observation()

    # Step the environment (2P) [pb low level]
    def _mock_step_2p(self, mov_p1, att_p1, mov_p2, att_p2):

        # Update class state
        self.new_game_state(mov_p1, att_p1, mov_p2, att_p2)

        return self.update_observation()

    # Closing DIAMBRA Arena
    def _mock_close(self):
        pass
