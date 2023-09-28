#!/usr/bin/env python
import pytest
import diambra.arena
from pytest_utils import generate_pytest_decorator_input
from diambra.arena import SpaceTypes, EnvironmentSettings, EnvironmentSettingsMultiAgent, WrappersSettings
from diambra.arena.utils.engine_mock import load_mocker
from diambra.arena.utils.gym_utils import available_games

# Example Usage:
# pytest
# (optional)
#    module.py (Run specific module)
#    -s (show output)
#    -k "expression" (filter tests using case-insensitive with parts of the test name and/or parameters values combined with boolean operators, e.g. "wrappers and doapp")

def func(settings, wrappers_settings, mocker):
    load_mocker(mocker)
    try:
        env = diambra.arena.make(settings.game_id, settings, wrappers_settings)
        env.close()

        print("COMPLETED SUCCESSFULLY!")
        return 0
    except Exception as e:
        print(e)
        print("ERROR, ABORTED.")
        return 1

wrappers_settings_var_order = ["no_op_max", "repeat_action", "normalize_reward", "normalization_factor",
                               "clip_reward", "no_attack_buttons_combinations", "frame_shape", "stack_frames", "dilation",
                               "add_last_action", "stack_actions", "scale", "role_relative",
                               "flatten", "filter_keys", "wrappers"]
games_dict = available_games(False)


ok_test_parameters = {
    "no_op_max": [0, 2],
    "repeat_action": [1, 4],
    "normalize_reward": [True, False],
    "normalization_factor": [0.2, 0.5],
    "clip_reward": [True, False],
    "no_attack_buttons_combinations": [True, False],
    "frame_shape": [(0, 0, 0), (84, 84, 1), (84, 84, 3), (84, 84, 0)],
    "stack_frames": [1, 5],
    "dilation": [1, 3],
    "add_last_action": [True, False],
    "stack_actions": [1, 6],
    "scale": [True, False],
    "role_relative": [True, False],
    "flatten": [True, False],
    "filter_keys": [[], ["stage", "own_side"]],
    "wrappers": [[]],
}

ko_test_parameters = {
    "no_op_max": [-1],
    "repeat_action": [True],
    "normalize_reward": ["True"],
    "normalization_factor": [-10],
    "clip_reward": [0.5],
    "no_attack_buttons_combinations": [-1],
    "frame_shape": [(0, 84, 3), (128, 0, 1)],
    "stack_frames": [0],
    "dilation": [0],
    "add_last_action": [10],
    "stack_actions": [-2],
    "scale": [10],
    "role_relative": [24],
    "flatten": [None],
    "filter_keys": [12],
    "wrappers": ["test"],
}

def pytest_generate_tests(metafunc):
    test_vars, values_list = generate_pytest_decorator_input(wrappers_settings_var_order, ok_test_parameters, ko_test_parameters)
    metafunc.parametrize(test_vars, values_list)

# Wrappers
@pytest.mark.parametrize("game_id", list(games_dict.keys()))
@pytest.mark.parametrize("step_ratio", [1])
@pytest.mark.parametrize("n_players", [1, 2])
@pytest.mark.parametrize("action_space", [SpaceTypes.DISCRETE, SpaceTypes.MULTI_DISCRETE])
def test_wrappers_settings(game_id, step_ratio, n_players, action_space, no_op_max, repeat_action,
                           normalize_reward, normalization_factor, clip_reward,
                           no_attack_buttons_combinations, frame_shape, stack_frames, dilation,
                           add_last_action, stack_actions, scale, role_relative,
                           flatten, filter_keys, wrappers, expected, mocker):

    # Env settings
    if (n_players == 1):
        settings = EnvironmentSettings()
    else:
        settings = EnvironmentSettingsMultiAgent()
    settings.game_id = game_id
    settings.step_ratio = step_ratio
    settings.action_space = action_space
    if n_players == 2:
        settings.action_space = (action_space, action_space)

    # Env wrappers settings
    wrappers_settings = WrappersSettings()
    wrappers_settings.no_op_max = no_op_max
    wrappers_settings.repeat_action = repeat_action
    wrappers_settings.normalize_reward = normalize_reward
    wrappers_settings.normalization_factor = normalization_factor
    wrappers_settings.clip_reward = clip_reward
    wrappers_settings.no_attack_buttons_combinations = no_attack_buttons_combinations
    wrappers_settings.frame_shape = frame_shape
    wrappers_settings.stack_frames = stack_frames
    wrappers_settings.dilation = dilation
    wrappers_settings.add_last_action = add_last_action
    wrappers_settings.stack_actions = 1 if add_last_action is False and expected == 0 else stack_actions
    wrappers_settings.scale = scale
    wrappers_settings.role_relative = role_relative
    wrappers_settings.flatten = flatten
    wrappers_settings.filter_keys = filter_keys
    wrappers_settings.wrappers = wrappers

    assert func(settings, wrappers_settings, mocker) == expected
