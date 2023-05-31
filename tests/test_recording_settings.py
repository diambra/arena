#!/usr/bin/env python
import pytest
from os.path import expanduser
import os
from diambra.arena.utils.engine_mock import DiambraEngineMock
import diambra.arena
from pytest_utils import generate_pytest_decorator_input
from diambra.arena.utils.gym_utils import available_games

# Example Usage:
# pytest
# (optional)
#    module.py (Run specific module)
#    -s (show output)
#    -k "expression" (filter tests using case-insensitive with parts of the test name and/or parameters values combined with boolean operators, e.g. "wrappers and doapp")

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

    diambra_engine_mock = DiambraEngineMock()

    mocker.patch("diambra.arena.engine.interface.DiambraEngine.__init__", diambra_engine_mock._mock__init__)
    mocker.patch("diambra.arena.engine.interface.DiambraEngine._env_init", diambra_engine_mock._mock_env_init)
    mocker.patch("diambra.arena.engine.interface.DiambraEngine._reset", diambra_engine_mock._mock_reset)
    mocker.patch("diambra.arena.engine.interface.DiambraEngine._step_1p", diambra_engine_mock._mock_step_1p)
    mocker.patch("diambra.arena.engine.interface.DiambraEngine._step_2p", diambra_engine_mock._mock_step_2p)
    mocker.patch("diambra.arena.engine.interface.DiambraEngine.close", diambra_engine_mock._mock_close)

    try:
        return env_exec(settings, wrappers_settings, traj_rec_settings)
    except Exception as e:
        print(e)
        return 1

wrappers_settings_var_order = ["username", "file_path", "ignore_p2"]
games_dict = available_games(False)
home_dir = expanduser("~")

ok_test_parameters = {
    "username": ["alexpalms", "test"],
    "file_path": [os.path.join(home_dir, "DIAMBRA")],
    "ignore_p2": [False, True],
}

ko_test_parameters = {
    "username": [123],
    "file_path": [True],
    "ignore_p2": [1],
}

def pytest_generate_tests(metafunc):
    test_vars, values_list_ok = generate_pytest_decorator_input(wrappers_settings_var_order, ok_test_parameters, 0)
    test_vars, values_list_ko = generate_pytest_decorator_input(wrappers_settings_var_order, ko_test_parameters, 1)
    values_list = values_list_ok + values_list_ko
    metafunc.parametrize(test_vars, values_list)


# Recording
@pytest.mark.parametrize("game_id", list(games_dict.keys()))
@pytest.mark.parametrize("player", ["Random", "P1P2"])
@pytest.mark.parametrize("hardcore", [False, True])
@pytest.mark.parametrize("action_space", ["discrete", "multi_discrete"])
@pytest.mark.parametrize("attack_buttons_combination", [False, True])
def test_settings_recording(game_id ,username, file_path, ignore_p2,
                            player, action_space, attack_buttons_combination, hardcore, expected, mocker):

    # Env settings
    settings = {}
    settings["game_id"] = game_id
    settings["player"] = player
    settings["hardcore"] = hardcore
    settings["action_space"] = action_space
    settings["attack_buttons_combination"] = attack_buttons_combination
    if player == "P1P2":
        settings["action_space"] = (action_space, action_space)
        settings["attack_buttons_combination"] = (attack_buttons_combination, attack_buttons_combination)

    # Env wrappers settings
    wrappers_settings = {}
    wrappers_settings["hwc_obs_resize"] = (128, 128, 1)
    wrappers_settings["reward_normalization"] = True
    wrappers_settings["frame_stack"] = 4
    wrappers_settings["actions_stack"] = 12
    wrappers_settings["scale"] = True

    # Recording settings
    traj_rec_settings = {}
    traj_rec_settings["username"] = username
    traj_rec_settings["file_path"] = file_path
    traj_rec_settings["ignore_p2"] = ignore_p2

    assert func(settings, wrappers_settings, traj_rec_settings, mocker) == expected
