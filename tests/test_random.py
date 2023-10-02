#!/usr/bin/env python3
import pytest
from env_exec_interface import env_exec
import random
from diambra.arena.utils.engine_mock import load_mocker
from diambra.arena import SpaceTypes, Roles, EnvironmentSettings, EnvironmentSettingsMultiAgent, WrappersSettings, RecordingSettings

# Example Usage:
# pytest
# (optional)
#    module.py (Run specific module)
#    -s (show output)
#    -k "expression" (filter tests using case-insensitive with parts of the test name and/or parameters values combined with boolean operators, e.g. "wrappers and doapp")

def func(game_id, n_players, action_space, frame_shape, wrappers_settings,
         no_action_probability, continue_games, use_mock_env, mocker):

    # Args
    args = {}
    args["interactive"] = False
    args["n_episodes"] = 1
    args["no_action_probability"] = no_action_probability
    args["render"] = False
    args["log_output"] = False

    if use_mock_env is True:
        override_perfect_probability = None
        if no_action_probability == 1.0:
            override_perfect_probability = 0.0
        load_mocker(mocker, override_perfect_probability=override_perfect_probability)

    try:
        # Settings
        if (n_players == 1):
            settings = EnvironmentSettings()
        else:
            settings = EnvironmentSettingsMultiAgent()
        settings.game_id = game_id
        settings.frame_shape = frame_shape
        settings.action_space = (action_space, action_space)
        if settings.n_players == 1:
            settings.action_space = settings.action_space[0]

        # Options (settings to change at reset)
        options_list = []
        roles = [[Roles.P1, Roles.P2], [Roles.P2, Roles.P1]]
        for role in roles:
            role_value = (role[0], role[1])
            if settings.n_players == 1:
                role_value = role_value[0]
                for continue_val in continue_games:
                    options_list.append({"role": role_value, "continue_game": continue_val})
            else:
                options_list.append({"role": role_value})

        return env_exec(settings, options_list, wrappers_settings, RecordingSettings(), args)
    except Exception as e:
        print(e)
        return 1

game_ids = ["doapp", "sfiii3n", "tektagt", "umk3", "samsh5sp", "kof98umh"]
n_players = [1, 2]
action_spaces = [SpaceTypes.DISCRETE, SpaceTypes.MULTI_DISCRETE]
no_action_probabilities = [0.0, 1.0]

@pytest.mark.parametrize("game_id", game_ids)
@pytest.mark.parametrize("n_players", n_players)
@pytest.mark.parametrize("action_space", action_spaces)
@pytest.mark.parametrize("no_action_probability", no_action_probabilities)
def test_random_gym_mock(game_id, n_players, action_space, no_action_probability, mocker):
    frame_shape = random.choice([(128, 128, 1), (256, 256, 0)])
    continue_games = [0.0]
    use_mock_env = True
    assert func(game_id, n_players, action_space, frame_shape, WrappersSettings(),
                no_action_probability, continue_games, use_mock_env, mocker) == 0

@pytest.mark.parametrize("game_id", game_ids)
@pytest.mark.parametrize("n_players", n_players)
@pytest.mark.parametrize("action_space", action_spaces)
@pytest.mark.parametrize("no_action_probability", no_action_probabilities)
def test_random_wrappers_mock(game_id, n_players, action_space, no_action_probability, mocker):
    frame_shape = random.choice([(128, 128, 1), (256, 256, 0)])
    continue_games = [0.0]
    use_mock_env = True

    # Env wrappers settings
    wrappers_settings = WrappersSettings()
    wrappers_settings.no_op_max = 0
    wrappers_settings.repeat_action = 1
    wrappers_settings.frame_shape = random.choice([(128, 128, 1), (256, 256, 0)])
    wrappers_settings.normalize_reward = True
    wrappers_settings.clip_reward = False
    wrappers_settings.stack_frames = 4
    wrappers_settings.dilation = 1
    wrappers_settings.add_last_action = True
    wrappers_settings.stack_actions = 12
    wrappers_settings.scale = True
    wrappers_settings.role_relative = True
    wrappers_settings.flatten = True
    suffix = ""
    if n_players == 2:
        suffix = "agent_0_"
    wrappers_settings.filter_keys = ["stage", "timer", suffix + "own_side", suffix + "opp_side",
                                     suffix + "opp_character", suffix + "action"]

    assert func(game_id, n_players, action_space, frame_shape, wrappers_settings,
                no_action_probability, continue_games, use_mock_env, mocker) == 0

@pytest.mark.parametrize("game_id", game_ids)
@pytest.mark.parametrize("n_players", n_players)
@pytest.mark.parametrize("action_space", action_spaces)
@pytest.mark.parametrize("no_action_probability", [0.0])
def test_random_integration(game_id, n_players, action_space, no_action_probability, mocker):
    frame_shape = random.choice([(128, 128, 1), (256, 256, 0)])
    continue_games = [-1.0, 0.0, 0.3]
    use_mock_env = False

    # Env wrappers settings
    wrappers_settings = WrappersSettings()
    wrappers_settings.no_op_max = 0
    wrappers_settings.repeat_action = 1
    wrappers_settings.frame_shape = (128, 128, 1)
    wrappers_settings.normalize_reward = True
    wrappers_settings.clip_reward = False
    wrappers_settings.stack_frames = 4
    wrappers_settings.dilation = 1
    wrappers_settings.add_last_action = True
    wrappers_settings.stack_actions = 12
    wrappers_settings.scale = True
    wrappers_settings.role_relative = True
    wrappers_settings.flatten = True
    suffix = ""
    if n_players == 2:
        suffix = "agent_0_"
    wrappers_settings.filter_keys = ["stage", "timer", suffix + "own_side", suffix + "opp_side",
                                     suffix + "opp_character", suffix + "action"]

    assert func(game_id, n_players, action_space, frame_shape, wrappers_settings,
                no_action_probability, continue_games, use_mock_env, mocker) == 0
