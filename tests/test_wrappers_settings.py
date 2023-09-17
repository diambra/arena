#!/usr/bin/env python
import pytest
import diambra.arena
from pytest_utils import generate_pytest_decorator_input
from diambra.arena import SpaceTypes
from diambra.arena.utils.engine_mock import load_mocker
from diambra.arena.utils.gym_utils import available_games

# Example Usage:
# pytest
# (optional)
#    module.py (Run specific module)
#    -s (show output)
#    -k "expression" (filter tests using case-insensitive with parts of the test name and/or parameters values combined with boolean operators, e.g. "wrappers and doapp")

def func(settings, wrappers_settings, episode_recording_settings, mocker):
    load_mocker(mocker)
    try:
        env = diambra.arena.make(settings["game_id"], settings, wrappers_settings, episode_recording_settings)
        env.close()

        print("COMPLETED SUCCESSFULLY!")
        return 0
    except Exception as e:
        print(e)
        print("ERROR, ABORTED.")
        return 1

wrappers_settings_var_order = ["no_op_max", "sticky_actions", "reward_normalization", "reward_normalization_factor",
                               "clip_rewards", "no_attack_buttons_combinations", "frame_shape", "frame_stack", "dilation",
                               "add_last_action_to_observation", "actions_stack", "scale", "role_relative_observation",
                               "flatten", "filter_keys", "wrappers"]
games_dict = available_games(False)


ok_test_parameters = {
    "no_op_max": [0, 2],
    "sticky_actions": [1, 4],
    "reward_normalization": [True, False],
    "reward_normalization_factor": [0.2, 0.5],
    "clip_rewards": [True, False],
    "no_attack_buttons_combinations": [True, False],
    "frame_shape": [(0, 0, 0), (84, 84, 1), (84, 84, 3), (84, 84, 0)],
    "frame_stack": [1, 5],
    "dilation": [1, 3],
    "add_last_action_to_observation": [True, False],
    "actions_stack": [1, 6],
    "scale": [True, False],
    "role_relative_observation": [True, False],
    "flatten": [True, False],
    "filter_keys": [[], ["stage", "own_side"]],
    "wrappers": [[]],
}

ko_test_parameters = {
    "no_op_max": [-1],
    "sticky_actions": [True],
    "reward_normalization": ["True"],
    "reward_normalization_factor": [-10],
    "clip_rewards": [0.5],
    "no_attack_buttons_combinations": [-1],
    "frame_shape": [(0, 84, 3), (128, 0, 1)],
    "frame_stack": [0],
    "dilation": [0],
    "add_last_action_to_observation": [10],
    "actions_stack": [-2],
    "scale": [10],
    "role_relative_observation": [24],
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
def test_wrappers_settings(game_id, step_ratio, n_players, action_space, no_op_max, sticky_actions,
                           reward_normalization, reward_normalization_factor, clip_rewards,
                           no_attack_buttons_combinations, frame_shape, frame_stack, dilation,
                           add_last_action_to_observation, actions_stack, scale, role_relative_observation,
                           flatten, filter_keys, wrappers, expected, mocker):

    # Env settings
    settings = {}
    settings["game_id"] = game_id
    settings["step_ratio"] = step_ratio
    settings["n_players"] = n_players
    settings["action_space"] = action_space
    if n_players == 2:
        settings["action_space"] = (action_space, action_space)

    # Env wrappers settings
    wrappers_settings = {}
    wrappers_settings["no_op_max"] = no_op_max
    wrappers_settings["sticky_actions"] = sticky_actions
    wrappers_settings["reward_normalization"] = reward_normalization
    wrappers_settings["reward_normalization_factor"] = reward_normalization_factor
    wrappers_settings["clip_rewards"] = clip_rewards
    wrappers_settings["no_attack_buttons_combinations"] = no_attack_buttons_combinations
    wrappers_settings["frame_shape"] = frame_shape
    wrappers_settings["frame_stack"] = frame_stack
    wrappers_settings["dilation"] = dilation
    wrappers_settings["add_last_action_to_observation"] = add_last_action_to_observation
    wrappers_settings["actions_stack"] = 1 if add_last_action_to_observation is False and expected == 0 else actions_stack
    wrappers_settings["scale"] = scale
    wrappers_settings["role_relative_observation"] = role_relative_observation
    wrappers_settings["flatten"] = flatten
    wrappers_settings["filter_keys"] = filter_keys
    wrappers_settings["wrappers"] = wrappers

    # Recording settings
    episode_recording_settings = {}

    assert func(settings, wrappers_settings, episode_recording_settings, mocker) == expected
