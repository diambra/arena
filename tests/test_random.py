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

def func(game_id, n_players, roles, continue_game, action_space, frame_shape, wrappers_settings,
         episode_recording_settings, no_action_probability, use_mock_env, mocker):

    # Args
    args = {}
    args["interactive"] = False
    args["n_episodes"] = 1
    args["no_action"] = random.choices([True, False], [no_action_probability, 1.0 - no_action_probability])[0]
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
        settings["role"] = (roles[0], roles[1])
        settings["continue_game"] = continue_game
        if settings["n_players"] == 1:
            settings["role"] = settings["role"][0]
            settings["action_space"] = settings["action_space"][0]

        return env_exec(settings, wrappers_settings, episode_recording_settings, args)
    except Exception as e:
        print(e)
        return 1

game_ids = ["doapp", "sfiii3n", "tektagt", "umk3", "samsh5sp", "kof98umh"]
n_players = [1, 2]
roles = [["P1", "P2"], ["P2", "P1"]]
continue_games = [-1.0, 0.0, 0.3]
action_spaces = ["discrete", "multi_discrete"]
no_action_probability = 0.5
episode_recording_probability = 0.5

@pytest.mark.parametrize("game_id", game_ids)
@pytest.mark.parametrize("n_players", n_players)
@pytest.mark.parametrize("roles", roles)
@pytest.mark.parametrize("continue_game", continue_games)
@pytest.mark.parametrize("action_space", action_spaces)
def test_random_gym_mock(game_id, n_players, roles, continue_game, action_space, mocker):
    frame_shape = random.choice([(128, 128, 1), (256, 256, 0)])
    use_mock_env = True
    wrappers_settings = {}
    episode_recording_settings = {}
    assert func(game_id, n_players, roles, continue_game, action_space, frame_shape, wrappers_settings,
                episode_recording_settings, no_action_probability, use_mock_env, mocker) == 0

@pytest.mark.parametrize("game_id", game_ids)
@pytest.mark.parametrize("n_players", n_players)
@pytest.mark.parametrize("roles", roles)
@pytest.mark.parametrize("action_space", action_spaces)
def test_random_wrappers_mock(game_id, n_players, roles, action_space, mocker):
    frame_shape = random.choice([(128, 128, 1), (256, 256, 0)])
    continue_game = 0.0
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

    # Recording settings
    home_dir = expanduser("~")
    episode_recording_settings = {}
    episode_recording_settings["username"] = "alexpalms"
    subfolder = game_id if use_mock_env is False else "mock"
    episode_recording_settings["dataset_path"] = os.path.join(home_dir, "DIAMBRA/episode_recording", subfolder)

    if (random.choices([True, False], [episode_recording_probability, 1.0 - episode_recording_probability])[0] is False):
        episode_recording_settings = {}

    assert func(game_id, n_players, roles, continue_game, action_space, frame_shape,
                wrappers_settings, episode_recording_settings, no_action_probability, use_mock_env, mocker) == 0

@pytest.mark.parametrize("game_id", game_ids)
@pytest.mark.parametrize("n_players", n_players)
@pytest.mark.parametrize("roles", roles)
@pytest.mark.parametrize("continue_game", continue_games)
@pytest.mark.parametrize("action_space", action_spaces)
def test_random_integration(game_id, n_players, roles, continue_game, action_space, mocker):
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

    # Recording settings
    home_dir = expanduser("~")
    episode_recording_settings = {}
    episode_recording_settings["username"] = "alexpalms"
    subfolder = game_id if use_mock_env is False else "mock"
    episode_recording_settings["dataset_path"] = os.path.join(home_dir, "DIAMBRA/episode_recording", subfolder)

    if (random.choices([True, False], [episode_recording_probability, 1.0 - episode_recording_probability])[0] is False):
        episode_recording_settings = {}

    assert func(game_id, n_players, roles, continue_game, action_space, frame_shape,
                wrappers_settings, episode_recording_settings, no_action_probability, use_mock_env, mocker) == 0