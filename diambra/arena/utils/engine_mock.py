import time
import random
import numpy as np
from diambra.engine import Client, model

class EngineMockParams:

    def __init__(self, round_winning_probability=0.4, perfect_probability=0.2,
                 steps_per_round=20, rounds_per_stage=2, stages_per_game=2,
                 number_of_chars=15, number_of_chars_per_round=1,
                 min_health=0, max_health=100,
                 frame_shape=[128, 128, 3], n_actions=[9, 7, 12], fps=1000):

        self.params = {}

        # Game features
        self.params["round_winning_probability"] = round_winning_probability
        self.params["perfect_probability"] = perfect_probability
        self.params["steps_per_round"] = steps_per_round
        self.params["rounds_per_stage"] = rounds_per_stage
        self.params["stages_per_game"] = stages_per_game
        self.params["number_of_chars"] = number_of_chars
        self.params["number_of_chars_per_round"] = number_of_chars_per_round
        self.params["min_health"] = min_health
        self.params["max_health"] = max_health
        self.params["frame_shape"] = frame_shape
        self.params["n_actions"] = n_actions
        self.params["fps"] = fps

class DiambraEngineMock:

    def __init__(self, engine_mock_params):

        # Game features
        self.round_winning_probability = engine_mock_params.params["round_winning_probability"]
        self.perfect_probability = engine_mock_params.params["perfect_probability"]
        self.steps_per_round = engine_mock_params.params["steps_per_round"]
        self.rounds_per_stage = engine_mock_params.params["rounds_per_stage"]
        self.stages_per_game = engine_mock_params.params["stages_per_game"]
        self.number_of_chars = engine_mock_params.params["number_of_chars"]
        self.number_of_chars_per_round = engine_mock_params.params["number_of_chars_per_round"]
        self.min_health = engine_mock_params.params["min_health"]
        self.max_health = engine_mock_params.params["max_health"]
        self.frame_shape = engine_mock_params.params["frame_shape"]
        self.n_actions = engine_mock_params.params["n_actions"]
        self.fps = engine_mock_params.params["fps"]

        time_dep_seed = int((time.time() - int(time.time() - 0.5)) * 1000)
        random.seed()

        # Class state variables
        self.char_list = ["Char{}".format(i) for i in range(self.number_of_chars)]
        self.n_steps = 0
        self.n_rounds_won = 0
        self.n_rounds_lost = 0
        self.n_stages = 0
        self.n_continue = 0
        self.char_p1 = 0
        self.char_p2 = 0
        self.side_p1 = 0
        self.side_p2 = 1
        self.health_p1 = self.max_health
        self.health_p2 = self.max_health
        self.player = "P1"

    def generate_frame(self):
        frame = np.ones((self.frame_shape), dtype=np.int8) * ((self.n_stages * self.rounds_per_stage + self.n_steps) % 255)
        return frame.tobytes()

    def generate_ram_states(self):

        ram_states = {}
        ram_states["stage"] = {"type": 1, "min": 1, "max": self.stages_per_game, "val": self.n_stages+1}
        ram_states["CharP1"] = {"type": 2, "min": 0, "max": self.number_of_chars-1, "val": self.char_p1}
        ram_states["CharP2"] = {"type": 2, "min": 0, "max": self.number_of_chars-1, "val": self.char_p2}
        ram_states["SideP1"] = {"type": 0, "min": 0, "max": 1, "val": self.side_p1}
        ram_states["SideP2"] = {"type": 0, "min": 0, "max": 1, "val": self.side_p2}
        ram_states["WinsP1"] = {"type": 1, "min": 0, "max": 2, "val": self.n_rounds_lost if self.player == "P2" else self.n_rounds_won}
        ram_states["WinsP2"] = {"type": 1, "min": 0, "max": 2, "val": self.n_rounds_won if self.player == "P2" else self.n_rounds_lost}
        if self.number_of_chars_per_round == 1:
            ram_states["HealthP1"] = {"type": 1, "min": self.min_health, "max": self.max_health, "val": self.health_p1}
            ram_states["HealthP2"] = {"type": 1, "min": self.min_health, "max": self.max_health, "val": self.health_p2}
        else:
            for idx in range(self.number_of_chars_per_round):
                ram_states["Health{}P1".format(idx+1)] = {"type": 1, "min": self.min_health, "max": self.max_health, "val": self.health_p1}
                ram_states["Health{}P2".format(idx+1)] = {"type": 1, "min": self.min_health, "max": self.max_health, "val": self.health_p2}

        return ram_states

    def _mock__init__(self, env_address, grpc_timeout=60):
        print("Trying to connect to DIAMBRA Engine server (timeout={}s)...".format(grpc_timeout))
        print("... done (MOCKED!).")

    # Send env settings, retrieve env info and int variables list [pb low level]
    def _mock_env_init(self, env_settings_pb):
        self.settings = env_settings_pb
        if (self.settings.frame_shape.h > 0 and self.settings.frame_shape.w > 0 ):
            self.frame_shape[0] = self.settings.frame_shape.h
            self.frame_shape[1] = self.settings.frame_shape.w
        if (self.settings.frame_shape.c == 1 or self.settings.frame_shape.c == 3):
            self.frame_shape[2] = self.settings.frame_shape.c

        self.continue_per_episode = - int(self.settings.continue_game) if self.settings.continue_game < 0.0 else int(self.settings.continue_game*10)

        # Build the response
        response = model.EnvInitResponse()

        response.available_actions.with_buttons_combination.moves = self.n_actions[0]
        response.available_actions.with_buttons_combination.attacks = self.n_actions[2]
        response.available_actions.without_buttons_combination.moves = self.n_actions[0]
        response.available_actions.without_buttons_combination.attacks = self.n_actions[1]

        response.frame_shape.h = self.frame_shape[0]
        response.frame_shape.w = self.frame_shape[1]
        response.frame_shape.c = self.frame_shape[2]
        response.delta_health = self.max_health - self.min_health
        response.max_stage = self.stages_per_game
        response.cumulative_reward_bounds.min = -((self.rounds_per_stage - 1) * (self.stages_per_game - 1) + self.rounds_per_stage) * (self.max_health - self.min_health)
        response.cumulative_reward_bounds.max = self.rounds_per_stage * self.stages_per_game * (self.max_health - self.min_health)
        response.char_list.extend(self.char_list)
        response.buttons.moves.extend(["NoMove", "Left", "UpLeft", "Up", "UpRight", "Right", "DownRight", "Down", "DownLeft"])
        response.buttons.attacks.extend(["But{}".format(i) for i in range(self.n_actions[1])] +\
                                        ["But{}But{}".format(i - self.n_actions[1] + 1, i - self.n_actions[1] + 2)\
                                        for i in range(self.n_actions[1], self.n_actions[2])])
        response.button_mapping.moves.extend(["0", " ", "1", "\u2190", "2", "\u2196", "3", "\u2191",
                                              "4", "\u2197", "5", "\u2192", "6", "\u2198", "7", "\u2193", "8", "\u2199"])
        attack_mapping = ["0", " "]
        for i in range(1, self.n_actions[2]):
            attack_mapping += [str(i), "Attack{}".format(i)]
        response.button_mapping.attacks.extend(attack_mapping)

        ram_states = self.generate_ram_states()
        for k, v in ram_states.items():
            response.ram_states[k].type = v["type"]
            response.ram_states[k].min = v["min"]
            response.ram_states[k].max = v["max"]
            response.ram_states[k].val = v["val"]

        return response

    # Set delta health
    def set_delta_health(self):
        # Setting delta health as a function of winning probabilities
        self.delta_health_p1 = 0.6
        self.delta_health_p2 = 0.6

        if self.player == "P2":
            self.delta_health_p1 *= self.round_winning_probability
            self.delta_health_p2 *= 1.0 - self.round_winning_probability
        else:
            self.delta_health_p1 *= 1.0 - self.round_winning_probability
            self.delta_health_p2 *= self.round_winning_probability

        if random.choices([True, False], [self.perfect_probability, 1.0 - self.perfect_probability])[0] is True:
            if self.player == "P2":
                self.delta_health_p2 = 0.0
            else:
                self.delta_health_p1 = 0.0

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
        self.set_delta_health()

        # Done flags
        self.round_done_ = False
        self.stage_done_ = False
        self.game_done_ = False
        self.episode_done_ = False
        self.env_done_ = False

        self.side_p1 = 0
        self.side_p2 = 1
        self.health_p1 = self.max_health
        self.health_p2 = self.max_health

        self.reward = 0

        # Characters
        if self.player == "P1P2":
            self.char_p1 = random.choices(range(self.number_of_chars))[0]
            self.char_p2 = random.choices(range(self.number_of_chars))[0]
        elif self.player == "P1":
            self.char_p1 = random.choices(range(self.number_of_chars))[0]
            self.char_p2 = self.n_stages
        else:
            self.char_p1 = self.n_stages
            self.char_p2 = random.choices(range(self.number_of_chars))[0]

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
        coeff_p1 = 1.0 - random.random() * self.delta_health_p1
        coeff_p2 = 1.0 - random.random() * self.delta_health_p2

        if att_p1 == 0:
            if self.player == "P2":
                coeff_p1 = 1
            else:
                coeff_p2 = 1

        if self.player == "P1P2" and att_p2 == 0:
                coeff_p1 = 1

        self.health_p1 = int(self.health_p1 * coeff_p1)
        self.health_p2 = int(self.health_p2 * coeff_p2)

        if (min(self.health_p1, self.health_p2) == 0) or ((self.n_steps % self.steps_per_round) == 0):
            self.round_done_ = True

            if self.health_p1 > self.health_p2:
                if self.player == "P2":
                    print("Round lost")
                    self.n_rounds_lost += 1
                else:
                    print("Round won")
                    self.n_rounds_won += 1

            elif self.health_p2 > self.health_p1:
                if self.player == "P2":
                    print("Round won")
                    self.n_rounds_won += 1
                else:
                    print("Round lost")
                    self.n_rounds_lost += 1

            else:
                print("Draw")
                self.n_rounds_won += 1
                self.n_rounds_lost += 1

        if self.n_rounds_won == self.rounds_per_stage:
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

        if self.n_rounds_lost == self.rounds_per_stage:
            self.game_done_ = True
            if self.n_continue >= self.continue_per_episode:
                self.episode_done_ = True
            else:
                self.n_continue += 1
                self.n_rounds_won = 0
                self.n_rounds_lost = 0

        if self.n_stages == self.stages_per_game:
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
            self.health_p1 = self.max_health
            self.health_p2 = self.max_health

            # Set delta healths
            self.set_delta_health()
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
        ram_states = self.generate_ram_states()
        for k, v in ram_states.items():
            observation.ram_states[k].type = v["type"]
            observation.ram_states[k].min = v["min"]
            observation.ram_states[k].max = v["max"]
            observation.ram_states[k].val = v["val"]

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