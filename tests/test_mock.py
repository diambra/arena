#!/usr/bin/env python3
import pytest
from env_exec_interface import env_exec
import sys
import random
from os.path import expanduser
import os
import logging
import numpy as np
from engine_mock import DiambraEngineMock

# Example Usage:
# pytest
# (optional)
#    module.py (Run specific module)
#    -s (show output)
#    -k 'expression' (filter tests using case-insensitive with parts of the test name and/or parameters values combined with boolean operators, e.g. 'wrappers and doapp')

def func(player, no_action_probability, mocker):

    # Args
    args = {}
    args["interactive_viz"] = False
    args["n_episodes"] = 1

    args["no_action"] = random.choices([True, False], [no_action_probability, 1.0 - no_action_probability])[0]

    round_winning_probability = 0.5
    perfect_probability=0.2
    if args["no_action"] is True:
        round_winning_probability = 0.0
        perfect_probability=0.0

    diambra_engine_mock = DiambraEngineMock(round_winning_probability, perfect_probability)

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
        settings["player"] = "P1"
        settings["step_ratio"] = 6
        settings["continue_game"] = 0.0
        settings["action_space"] = ["discrete", "discrete"]
        settings["attack_but_combination"] = [True, True]
        if settings["player"] != "P1P2":
            settings["action_space"] = settings["action_space"][0]
            settings["attack_but_combination"] = settings["attack_but_combination"][0]
        settings["hardcore"] = False

        return env_exec(settings, {}, {}, args)

        return 0
    except Exception as e:
        print(e)
        return 1

players = ["Random"]
no_action_probability = 1.0

@pytest.mark.parametrize("player", players)
def test_random_gym(player, mocker):
    assert func(player, no_action_probability, mocker) == 0

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