#!/usr/bin/env python
import pytest
import diambra.arena
from pytest_utils import generate_pytest_decorator_input, load_mocker
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

wrappers_settings_var_order = ["no_op_max", "sticky_actions", "frame_shape", "reward_normalization",
                               "reward_normalization_factor", "clip_rewards", "frame_stack", "dilation",
                               "actions_stack", "scale", "scale_mod", "flatten", "filter_keys"]
games_dict = available_games(False)


ok_test_parameters = {
    "no_op_max": [0, 2],
    "sticky_actions": [1, 4],
    "frame_shape": [(0, 0, 0), (84, 84, 1), (84, 84, 3), (84, 84, 0)],
    "reward_normalization": [True, False],
    "reward_normalization_factor": [0.2, 0.5],
    "clip_rewards": [True, False],
    "frame_stack": [1, 5],
    "dilation": [1, 3],
    "actions_stack": [1, 6],
    "scale": [True, False],
    "scale_mod": [0],
    "flatten": [True, False],
    "filter_keys": [[], ["stage", "own_side"]]
}

ko_test_parameters = {
    "no_op_max": [-1],
    "sticky_actions": [True],
    "frame_shape": [(0, 84, 3), (0, 0, 1)], # TODO: FIXME: the second value is OK
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
@pytest.mark.parametrize("game_id", list(games_dict.keys()))
@pytest.mark.parametrize("step_ratio", [1])
@pytest.mark.parametrize("n_players", [1, 2])
@pytest.mark.parametrize("action_space", ["discrete", "multi_discrete"])
def test_wrappers_settings(game_id, step_ratio, n_players, action_space, no_op_max, sticky_actions,
                           frame_shape, reward_normalization, reward_normalization_factor,
                           clip_rewards, frame_stack, dilation, actions_stack, scale, scale_mod,
                           flatten, filter_keys, expected, mocker):

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
    wrappers_settings["frame_shape"] = frame_shape
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
    episode_recording_settings = {}

    assert func(settings, wrappers_settings, episode_recording_settings, mocker) == expected
