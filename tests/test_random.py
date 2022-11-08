#!/usr/bin/env python3
import pytest
from env_exec_interface import env_exec
import sys
import random
from os.path import expanduser
import os
from engine_mock import DiambraEngineMock

# Example Usage:
# pytest
# (optional)
#    module.py (Run specific module)
#    -s (show output)
#    -k 'expression' (filter tests using case-insensitive with parts of the test name and/or parameters values combined with boolean operators, e.g. 'wrappers and doapp')

def func(player, continue_game, action_space, attack_buttons_combination,
         wrappers_settings, traj_rec_settings, hardcore_prob, no_action_prob, mocker):

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
        # Settings
        settings = {}
        settings["game_id"] = "mock"
        settings["player"] = player
        settings["continue_game"] = continue_game
        settings["action_space"] = [action_space, action_space]
        settings["attack_but_combination"] = [attack_buttons_combination, attack_buttons_combination]
        if settings["player"] != "P1P2":
            settings["action_space"] = settings["action_space"][0]
            settings["attack_but_combination"] = settings["attack_but_combination"][0]
        settings["hardcore"] = random.choices([True, False], [hardcore_probability, 1.0 - hardcore_probability])[0]

        return env_exec(settings, wrappers_settings, traj_rec_settings, args)

        return 0
    except Exception as e:
        print(e)
        return 1

#game_ids = ["doapp", "sfiii3n", "tektagt", "umk3", "samsh5sp", "kof98umh"] # To substitute with game (mocked) features
players = ["Random", "P1P2"]
continue_games = [-1.0, 0.0, 0.3]
action_spaces = ["discrete", "multi_discrete"]
attack_buttons_combinations = [False, True]
hardcore_probability = 0.4
no_action_probability = 0.5
rec_traj_probability = 0.5

@pytest.mark.parametrize("player", players)
@pytest.mark.parametrize("continue_game", continue_games)
@pytest.mark.parametrize("action_space", action_spaces)
@pytest.mark.parametrize("attack_buttons_combination", attack_buttons_combinations)
def test_random_gym(player, continue_game, action_space, attack_buttons_combination, mocker):
    wrappers_settings = {}
    traj_rec_settings = {}
    assert func(player, continue_game, action_space, attack_buttons_combination,
                wrappers_settings, traj_rec_settings, hardcore_probability, no_action_probability, mocker) == 0

@pytest.mark.parametrize("player", players)
@pytest.mark.parametrize("continue_game", continue_games)
@pytest.mark.parametrize("action_space", action_spaces)
@pytest.mark.parametrize("attack_buttons_combination", attack_buttons_combinations)
def test_random_wrappers(player, continue_game, action_space, attack_buttons_combination, mocker):

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
                                        "P1_ownHealth", "P1_oppHealth", "P1_oppChar",
                                        "P1_actions_move", "P1_actions_attack"]

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
