#!/usr/bin/env python3
import pytest
import random
import diambra.arena
from diambra.arena.utils.engine_mock import DiambraEngineMock
from diambra.arena.utils.gym_utils import available_games
from pytest_utils import generate_pytest_decorator_input

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

games_dict = available_games(False)
gym_settings_var_order = ["player", "step_ratio", "frame_shape", "tower", "super_art",
                          "fighting_style", "ultimate_style", "continue_game", "action_space",
                          "attack_buttons_combination"]

ok_test_parameters = {
    "continue_game": [-1.0, 0.0, 0.3],
    "action_space": ["discrete", "multi_discrete"],
    "attack_buttons_combination": [False, True],
    "player": ["P1", "P2", "Random", "P1P2"],
    "step_ratio": [1, 3, 6],
    "frame_shape": [(0, 0, 0), (0, 0, 1), (82, 82, 0), (82, 82, 1)],
    "tower": [1, 3, 4],
    "super_art": [0, 1, 3],
    "fighting_style": [0, 1, 3],
    "ultimate_style": [(0, 0, 0), (1, 2, 0), (2, 2, 2)],
}

ko_test_parameters = {
    "continue_game": [1.3, "string"],
    "action_space": ["random", 12],
    "attack_buttons_combination": [1],
    "player": [4, "P2P1"],
    "step_ratio": [8],
    "frame_shape": [(0, 82, 0), (0, 0, 4), (-100, -100, 3)],
    "tower": [5],
    "super_art": ["value", 4],
    "fighting_style": [False, 6],
    "ultimate_style": [(10, 0, 0), "string"],
}

def pytest_generate_tests(metafunc):
    test_vars, values_list_ok = generate_pytest_decorator_input(gym_settings_var_order, ok_test_parameters, 0)
    test_vars, values_list_ko = generate_pytest_decorator_input(gym_settings_var_order, ko_test_parameters, 1)
    values_list = values_list_ok + values_list_ko
    metafunc.parametrize(test_vars, values_list)

# Gym
@pytest.mark.parametrize("game_id", list(games_dict.keys()))
def test_settings_gym(game_id, player, step_ratio, frame_shape, tower, super_art,
                      fighting_style, ultimate_style, continue_game, action_space,
                      attack_buttons_combination, expected, mocker):

    game_data = games_dict[game_id]
    difficulty_range = range(game_data["difficulty"][0], game_data["difficulty"][1] + 1)
    characters_list = ["Random"] + game_data["char_list"]
    outfits_range = range(game_data["outfits"][0], game_data["outfits"][1] + 1)
    difficulty = random.choice(difficulty_range)
    characters = random.choice(characters_list)
    char_outfits = random.choice(outfits_range)

    # Env settings
    settings = {}
    settings["game_id"] = game_id
    settings["player"] = player
    settings["step_ratio"] = step_ratio
    settings["continue_game"] = continue_game
    settings["difficulty"] = difficulty
    settings["frame_shape"] = frame_shape

    settings["tower"] = tower

    settings["characters"] = (characters, characters)
    settings["char_outfits"] = (char_outfits, char_outfits)
    settings["action_space"] = (action_space, action_space)
    settings["attack_but_combination"] = (attack_buttons_combination, attack_buttons_combination)

    settings["super_art"] = (super_art, super_art)
    settings["fighting_style"] = (fighting_style, fighting_style)
    settings["ultimate_style"] = (ultimate_style, ultimate_style)

    if settings["player"] != "P1P2":
        for key in ["characters" , "char_outfits", "action_space", "attack_but_combination",
                    "super_art", "fighting_style", "ultimate_style"]:
            settings[key] = settings[key][0]

    wrappers_settings = {}
    traj_rec_settings = {}

    assert func(settings, wrappers_settings, traj_rec_settings, mocker) == expected
