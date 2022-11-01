#!/usr/bin/env python3
import pytest
from env_exec_interface import env_exec
import sys
import time
import random
from os.path import expanduser
import os
import logging
import numpy as np

from diambra.engine import Client, model
import grpc

# Example Usage:
# pytest
# (optional)
#    module.py (Run specific module)
#    -s (show output)
#    -k 'expression' (filter tests using case-insensitive with parts of the test name and/or parameters values combined with boolean operators, e.g. 'wrappers and doapp')

class DiambraEngineMock:

    def __init__(self):
        # Game features
        self.steps_per_round = 20
        self.rounds_per_stage = 2
        self.stages_per_game = 2
        self.number_of_chars = 15
        self.char_list = ["Char{}".format(i) for i in range(self.number_of_chars)]
        self.min_health = 0
        self.max_health = 100
        self.frame_shape = [128, 128, 3]
        self.n_actions = [9, 7, 12]

        self.round_winning_probability = 0.7
        self.perfect_probability = 0.3

        # Class state variables
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
        frame = np.ones((self.frame_shape), dtype=np.int8) * self.n_steps
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
        ram_states["HealthP1"] = {"type": 1, "min": self.min_health, "max": self.max_health, "val": self.health_p1}
        ram_states["HealthP2"] = {"type": 1, "min": self.min_health, "max": self.max_health, "val": self.health_p2}

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

        if (self.n_steps % self.steps_per_round) == 0:
            self.round_done_ = True
            if random.choices([True, False], [self.round_winning_probability, 1 - self.round_winning_probability])[0] is True:
                print("Round won")
                self.n_rounds_won += 1

                if self.player == "P2":
                    self.health_p1 = 0
                    if random.choices([True, False], [self.perfect_probability, 1 - self.perfect_probability])[0] is True:
                        self.health_p2 = self.max_health
                        starting_health_p2 = self.health_p2
                else:
                    self.health_p2 = 0
                    if random.choices([True, False], [self.perfect_probability, 1 - self.perfect_probability])[0] is True:
                        self.health_p1 = self.max_health
                        starting_health_p1 = self.health_p1

            else:
                print("Round lost")
                self.n_rounds_lost += 1
                if self.player == "P2":
                    self.health_p2 = 0
                else:
                    self.health_p1 = 0
        else:
            self.health_p1 = int(self.health_p1 * random.choices([0.7, 0.8, 0.9])[0])
            self.health_p2 = int(self.health_p2 * random.choices([0.7, 0.8, 0.9])[0])

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

        delta_p1 = starting_health_p1 - self.health_p1
        delta_p2 = starting_health_p2 - self.health_p2
        self.reward = delta_p1 - delta_p2 if self.player == "P2" else delta_p2 - delta_p1

        if np.any([self.round_done_, self.stage_done_, self.game_done_]) is True:
            self.side_p1 = 0
            self.side_p2 = 1
            self.health_p1 = self.max_health
            self.health_p2 = self.max_health
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

def func(player, mocker):

    diambra_engine_mock = DiambraEngineMock()

    mocker.patch('diambra.arena.engine.interface.DiambraEngine.__init__', diambra_engine_mock._mock__init__)
    mocker.patch('diambra.arena.engine.interface.DiambraEngine._env_init', diambra_engine_mock._mock_env_init)
    mocker.patch('diambra.arena.engine.interface.DiambraEngine._reset', diambra_engine_mock._mock_reset)
    mocker.patch('diambra.arena.engine.interface.DiambraEngine._step_1p', diambra_engine_mock._mock_step_1p)
    mocker.patch('diambra.arena.engine.interface.DiambraEngine._step_2p', diambra_engine_mock._mock_step_2p)
    mocker.patch('diambra.arena.engine.interface.DiambraEngine.close', diambra_engine_mock._mock_close)

    try:
        viz_flag = True
        wait_key = 1

        # Settings
        settings = {}
        settings["game_id"] = "doapp"
        settings["player"] = "Random"
        settings["step_ratio"] = 6
        settings["action_space"] = ["discrete", "discrete"]
        settings["attack_but_combination"] = [True, True]
        if settings["player"] != "P1P2":
            settings["action_space"] = settings["action_space"][0]
            settings["attack_but_combination"] = settings["attack_but_combination"][0]
        settings["hardcore"] = False

        # Args
        args = {}
        args["interactive_viz"] = True
        args["no_action_probability"] = 0.5
        args["n_episodes"] = 1

        return env_exec(settings, {}, {}, args)

        return 0
    except Exception as e:
        print(e)
        return 1

players = ["Random"]

@pytest.mark.parametrize("player", players)
def test_random_gym(player, mocker):
    assert func(player, mocker) == 0

'''
Current tests:
- Side at round end
- Cumulative reward (normal and no action)

Things to test:
- Gym:
    - Sampling from action space and using sample to run step
    - Check correct handling of ram states

- Wrappers:
    - Frame warping
    - Frame stacking
        - Normal
            - Frames equality at round end
        - With dilation
    - Action stacking
        - NoAction stack at round end
    - Scaling
        - Normal
        - Excluding image scaling
        - Processing discrete binary obs
    - Flattening and filtering
    - Action Sticking
    - Reward normalization
    - Reward clipping

'''