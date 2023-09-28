#!/usr/bin/env python
import pytest
from os.path import expanduser
import os
import diambra.arena
from diambra.arena import SpaceTypes, EnvironmentSettings, EnvironmentSettingsMultiAgent, WrappersSettings, RecordingSettings
from pytest_utils import generate_pytest_decorator_input
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
        env = diambra.arena.make(settings.game_id, settings, wrappers_settings, episode_recording_settings)
        env.close()

        print("COMPLETED SUCCESSFULLY!")
        return 0
    except Exception as e:
        print(e)
        print("ERROR, ABORTED.")
        return 1

episode_recording_settings_var_order = ["username", "dataset_path"]
games_dict = available_games(False)
home_dir = expanduser("~")

ok_test_parameters = {
    "username": ["alexpalms", "test"],
    "dataset_path": [os.path.join(home_dir, "DIAMBRA")],
}

ko_test_parameters = {
    "username": [123],
    "dataset_path": [True],
}

def pytest_generate_tests(metafunc):
    test_vars, values_list = generate_pytest_decorator_input(episode_recording_settings_var_order, ok_test_parameters, ko_test_parameters)
    metafunc.parametrize(test_vars, values_list)


# Recording
@pytest.mark.parametrize("game_id", list(games_dict.keys()))
@pytest.mark.parametrize("n_players", [1, 2])
@pytest.mark.parametrize("action_space", [SpaceTypes.DISCRETE, SpaceTypes.MULTI_DISCRETE])
def test_settings_recording(game_id ,username, dataset_path, n_players, action_space, expected, mocker):
    # Env settings
    if (n_players == 1):
        settings = EnvironmentSettings()
    else:
        settings = EnvironmentSettingsMultiAgent()
    settings.game_id = game_id
    settings.action_space = action_space
    if n_players == 2:
        settings.action_space = (action_space, action_space)

    # Env wrappers settings
    wrappers_settings = WrappersSettings()
    wrappers_settings.frame_shape = (128, 128, 1)
    wrappers_settings.normalize_reward = True
    wrappers_settings.stack_frames = 4
    wrappers_settings.add_last_action = True
    wrappers_settings.stack_actions = 12
    wrappers_settings.scale = True

    # Recording settings
    episode_recording_settings = RecordingSettings()
    episode_recording_settings.username = username
    episode_recording_settings.dataset_path = dataset_path

    assert func(settings, wrappers_settings, episode_recording_settings, mocker) == expected
