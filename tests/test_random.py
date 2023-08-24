#!/usr/bin/env python3
import pytest
from env_exec_interface import env_exec
import random
from os.path import expanduser
from pytest_utils import load_mocker
import os

# Example Usage:
# pytest
# (optional)
#    module.py (Run specific module)
#    -s (show output)
#    -k "expression" (filter tests using case-insensitive with parts of the test name and/or parameters values combined with boolean operators, e.g. "wrappers and doapp")

def func(game_id, n_players, action_space, frame_shape, wrappers_settings,
         no_action_probability, use_mock_env, mocker):

    # Args
    args = {}
    args["interactive"] = False
    args["n_episodes"] = 1
    args["no_action_probability"] = no_action_probability
    args["render"] = False

    if use_mock_env is True:
        load_mocker(mocker)

    try:
        # Settings
        settings = {}
        settings["game_id"] = game_id
        settings["frame_shape"] = frame_shape
        settings["n_players"] = n_players
        settings["action_space"] = (action_space, action_space)
        if settings["n_players"] == 1:
            settings["action_space"] = settings["action_space"][0]

        # Options (settings to change at reset)
        options_list = []
        roles = [["P1", "P2"], ["P2", "P1"]]
        continue_games = [-1.0, 0.0, 0.3]
        for role in roles:
            role_value = (role[0], role[1])
            if settings["n_players"] == 1:
                role_value = role_value[0]
                for continue_val in continue_games:
                    options_list.append({"role": role_value, "continue_game": continue_val})
            else:
                options_list.append({"role": role_value})

        return env_exec(settings, options_list, wrappers_settings, {}, args)
    except Exception as e:
        print(e)
        return 1

game_ids = ["doapp", "sfiii3n", "tektagt", "umk3", "samsh5sp", "kof98umh"]
n_players = [1, 2]
action_spaces = ["discrete", "multi_discrete"]
no_action_probability = 0.25

@pytest.mark.parametrize("game_id", game_ids)
@pytest.mark.parametrize("n_players", n_players)
@pytest.mark.parametrize("action_space", action_spaces)
def test_random_gym_mock(game_id, n_players, action_space, mocker):
    frame_shape = random.choice([(128, 128, 1), (256, 256, 0)])
    use_mock_env = True
    wrappers_settings = {}
    assert func(game_id, n_players, action_space, frame_shape, wrappers_settings,
                no_action_probability, use_mock_env, mocker) == 0

@pytest.mark.parametrize("game_id", game_ids)
@pytest.mark.parametrize("n_players", n_players)
@pytest.mark.parametrize("action_space", action_spaces)
def test_random_wrappers_mock(game_id, n_players, action_space, mocker):
    frame_shape = random.choice([(128, 128, 1), (256, 256, 0)])
    use_mock_env = True

    # Env wrappers settings
    wrappers_settings = {}
    wrappers_settings["no_op_max"] = 0
    wrappers_settings["sticky_actions"] = 1
    wrappers_settings["frame_shape"] = random.choice([(128, 128, 1), (256, 256, 0)])
    wrappers_settings["reward_normalization"] = True
    wrappers_settings["clip_rewards"] = False
    wrappers_settings["frame_stack"] = 4
    wrappers_settings["dilation"] = 1
    wrappers_settings["actions_stack"] = 12
    wrappers_settings["scale"] = True
    wrappers_settings["scale_mod"] = 0
    wrappers_settings["flatten"] = True
    suffix = ""
    if n_players == 2:
        suffix = "agent_0_"
    wrappers_settings["filter_keys"] = ["stage", "timer", suffix+"own_side", suffix+"opp_side",
                                        suffix+"opp_char", suffix+"action_move", suffix+"action_attack"]

    assert func(game_id, n_players, action_space, frame_shape, wrappers_settings,
                no_action_probability, use_mock_env, mocker) == 0

@pytest.mark.parametrize("game_id", game_ids)
@pytest.mark.parametrize("n_players", n_players)
@pytest.mark.parametrize("action_space", action_spaces)
def test_random_integration(game_id, n_players, action_space, mocker):
    frame_shape = random.choice([(128, 128, 1), (256, 256, 0)])
    use_mock_env = False

    # Env wrappers settings
    wrappers_settings = {}
    wrappers_settings["no_op_max"] = 0
    wrappers_settings["sticky_actions"] = 1
    wrappers_settings["frame_shape"] = (128, 128, 1)
    wrappers_settings["reward_normalization"] = True
    wrappers_settings["clip_rewards"] = False
    wrappers_settings["frame_stack"] = 4
    wrappers_settings["dilation"] = 1
    wrappers_settings["actions_stack"] = 12
    wrappers_settings["scale"] = True
    wrappers_settings["scale_mod"] = 0
    wrappers_settings["flatten"] = True
    suffix = ""
    if n_players == 2:
        suffix = "agent_0_"
    wrappers_settings["filter_keys"] = ["stage", "timer", suffix+"own_side", suffix+"opp_side",
                                        suffix+"opp_char", suffix+"action_move", suffix+"action_attack"]

    assert func(game_id, n_players, action_space, frame_shape, wrappers_settings,
                no_action_probability, use_mock_env, mocker) == 0