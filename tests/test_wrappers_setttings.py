#!/usr/bin/env python
import pytest
import sys
import random
from os.path import expanduser
import os
from engine_mock import DiambraEngineMock, EngineMockParams
import diambra.arena
import numpy as np
from pytest_utils import generate_pytest_decorator_input

# Example Usage:
# pytest
# (optional)
#    module.py (Run specific module)
#    -s (show output)
#    -k 'expression' (filter tests using case-insensitive with parts of the test name and/or parameters values combined with boolean operators, e.g. 'wrappers and doapp')

def env_exec(settings, wrappers_settings, traj_rec_settings):
    try:
        env = diambra.arena.make(settings["game_id"], settings, wrappers_settings, traj_rec_settings)
        env.close()

        print("COMPLETED SUCCESSFULLY!")
        return 0
    except Exception as e:
        print(e)
        print("ERROR, ABORTED.")
        return 1

def func(settings, wrappers_settings, traj_rec_settings, mocker):

    diambra_engine_mock_params = EngineMockParams()
    diambra_engine_mock = DiambraEngineMock(diambra_engine_mock_params)

    mocker.patch('diambra.arena.engine.interface.DiambraEngine.__init__', diambra_engine_mock._mock__init__)
    mocker.patch('diambra.arena.engine.interface.DiambraEngine._env_init', diambra_engine_mock._mock_env_init)
    mocker.patch('diambra.arena.engine.interface.DiambraEngine._reset', diambra_engine_mock._mock_reset)
    mocker.patch('diambra.arena.engine.interface.DiambraEngine._step_1p', diambra_engine_mock._mock_step_1p)
    mocker.patch('diambra.arena.engine.interface.DiambraEngine._step_2p', diambra_engine_mock._mock_step_2p)
    mocker.patch('diambra.arena.engine.interface.DiambraEngine.close', diambra_engine_mock._mock_close)

    try:
        return env_exec(settings, wrappers_settings, traj_rec_settings)

        return 0
    except Exception as e:
        print(e)
        return 1

wrappers_settings_var_order = ["no_op_max", "sticky_actions", "hwc_obs_resize", "reward_normalization",
                               "reward_normalization_factor", "clip_rewards", "frame_stack", "dilation",
                               "actions_stack", "scale", "scale_mod", "flatten", "filter_keys"]

ok_test_parameters = {
    "no_op_max": [0, 2],
    "sticky_actions": [1, 4],
    "hwc_obs_resize": [(0, 0, 0), (84, 84, 1), (84, 84, 3), (84, 84, 0)],
    "reward_normalization": [True, False],
    "reward_normalization_factor": [0.2, 0.5],
    "clip_rewards": [True, False],
    "frame_stack": [1, 5],
    "dilation": [1, 3],
    "actions_stack": [1, 6],
    "scale": [True, False],
    "scale_mod": [0],
    "flatten": [True, False],
    "filter_keys": [[], ["stage", "P1_ownSide"]]
}

ko_test_parameters = {
    "no_op_max": [-1],
    "sticky_actions": [True],
    "hwc_obs_resize": [(0, 84, 3), (0, 0, 1)],
    "reward_normalization": ["True"],
    "reward_normalization_factor": [-10],
    "clip_rewards": [0.5],
    "frame_stack": [0],
    "dilation": [0],
    "actions_stack": [-2],
    "scale": [10],
    "scale_mod": [2],
    "flatten": [None],
    "filter_keys": [12]
}

def pytest_generate_tests(metafunc):
    test_vars, values_list_ok = generate_pytest_decorator_input(wrappers_settings_var_order, ok_test_parameters, 0)
    test_vars, values_list_ko = generate_pytest_decorator_input(wrappers_settings_var_order, ko_test_parameters, 1)
    values_list = values_list_ok + values_list_ko
    metafunc.parametrize(test_vars, values_list)

# Wrappers
@pytest.mark.parametrize("step_ratio", [1])
@pytest.mark.parametrize("player", ["Random", "P1P2"])
@pytest.mark.parametrize("hardcore", [False, True])
@pytest.mark.parametrize("action_space", ["discrete", "multi_discrete"])
@pytest.mark.parametrize("attack_buttons_combination", [False, True])
def test_settings_wrappers(step_ratio, player, action_space, attack_buttons_combination, hardcore,
                           no_op_max, sticky_actions, hwc_obs_resize, reward_normalization,
                           reward_normalization_factor, clip_rewards, frame_stack, dilation,
                           actions_stack, scale, scale_mod, flatten, filter_keys, expected, mocker):

    # Env settings
    settings = {}
    settings["game_id"] = "doapp"
    settings["step_ratio"] = step_ratio
    settings["player"] = player
    settings["hardcore"] = hardcore
    settings["action_space"] = action_space
    settings["attack_buttons_combination"] = attack_buttons_combination
    if player == "P1P2":
        settings["action_space"] = (action_space, action_space)
        settings["attack_buttons_combination"] = (attack_buttons_combination, attack_buttons_combination)

    # Env wrappers settings
    wrappers_settings = {}
    wrappers_settings["no_op_max"] = no_op_max
    wrappers_settings["sticky_actions"] = sticky_actions
    wrappers_settings["hwc_obs_resize"] = hwc_obs_resize
    wrappers_settings["reward_normalization"] = reward_normalization
    wrappers_settings["clip_rewards"] = clip_rewards
    wrappers_settings["frame_stack"] = frame_stack
    wrappers_settings["dilation"] = dilation
    wrappers_settings["actions_stack"] = actions_stack
    wrappers_settings["scale"] = scale
    wrappers_settings["scale_mod"] = scale_mod
    wrappers_settings["flatten"] = flatten
    wrappers_settings["filter_keys"] = filter_keys

    # Recording settings
    traj_rec_settings = {}

    assert func(settings, wrappers_settings, traj_rec_settings, mocker) == expected


'''
@pytest.mark.parametrize("player", players)
@pytest.mark.parametrize("continue_game", continue_games)
@pytest.mark.parametrize("action_space", action_spaces)
@pytest.mark.parametrize("attack_buttons_combination", attack_buttons_combinations)
def test_settings_wrappers_1p_ok(player, continue_game, action_space, attack_buttons_combination, mocker):

    # Env wrappers settings
    wrappers_settings = {}
    wrappers_settings["no_op_max"] = 0
    wrappers_settings["sticky_actions"] = 1
    wrappers_settings["hwc_obs_resize"] = [128, 128, 1]
    wrappers_settings["reward_normalization"] = True
    wrappers_settings["clip_rewards"] = False
    wrappers_settings["frame_stack"] = 4
    wrappers_settings["dilation"] = 1
    wrappers_settings["actions_stack"] = 12
    wrappers_settings["scale"] = True
    wrappers_settings["scale_mod"] = 0
    wrappers_settings["flatten"] = True
    wrappers_settings["filter_keys"] = ["stage", "P1_ownSide", "P1_oppSide", "P1_oppSide",
                                        "P1_oppChar", "P1_actions_move", "P1_actions_attack"]

    # Recording settings
    home_dir = expanduser("~")
    traj_rec_settings = {}
    traj_rec_settings["user_name"] = "Alex"
    traj_rec_settings["file_path"] = os.path.join(home_dir, "DIAMBRA/trajRecordings/mock")
    traj_rec_settings["ignore_p2"] = 0
    traj_rec_settings["commit_hash"] = "0000000"

    if (random.choices([True, False], [rec_traj_probability, 1.0 - rec_traj_probability])[0] is False):
        traj_rec_settings = {}

    assert func(player, continue_game, action_space, attack_buttons_combination,
                wrappers_settings, traj_rec_settings, hardcore_probability, no_action_probability, mocker) == 0
'''