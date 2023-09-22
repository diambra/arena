#!/usr/bin/env python3
import pytest
import random
import diambra.arena
from diambra.arena import SpaceTypes, Roles, EnvironmentSettings, EnvironmentSettingsMultiAgent
from diambra.arena.utils.gym_utils import available_games
from pytest_utils import generate_pytest_decorator_input
from diambra.arena.utils.engine_mock import load_mocker

# Example Usage:
# pytest
# (optional)
#    module.py (Run specific module)
#    -s (show output)
#    -k "expression" (filter tests using case-insensitive with parts of the test name and/or parameters values combined with boolean operators, e.g. "wrappers and doapp")

def func(settings, mocker):
    load_mocker(mocker)
    try:
        env = diambra.arena.make(settings.game_id, settings)
        env.reset()
        env.close()
        print("COMPLETED SUCCESSFULLY!")
        return 0
    except Exception as e:
        print(e)
        print("ERROR, ABORTED.")
        return 1

games_dict = available_games(False)
gym_settings_var_order = ["frame_shape", "step_ratio", "action_space", "difficulty", "continue_game",
                          "tower", "role", "characters", "super_art", "fighting_style", "ultimate_style"]

ok_test_parameters = {
    "frame_shape": [(0, 0, 0), (0, 0, 1), (82, 82, 0), (82, 82, 1)],
    "step_ratio": [1, 3, 6],
    "action_space": [SpaceTypes.DISCRETE, SpaceTypes.MULTI_DISCRETE],
    "difficulty": [None, 1, 3],
    "continue_game": [-1.0, 0.0, 0.3],
    "tower": [1, 3, 4],
    "role": [[Roles.P1, Roles.P2], [Roles.P2, Roles.P1], [None, None]],
    "characters": [[None, None], [None, "TBD"], ["TBD", "TBD"]],
    "super_art": [None, 1, 3],
    "fighting_style": [None, 1, 3],
    "ultimate_style": [None, (2, 2, 2)],
}

ko_test_parameters = {
    "frame_shape": [(0, 82, 0), (0, 0, 4), (-100, -100, 3)],
    "step_ratio": [8],
    "difficulty": [True, 0, "Random"],
    "action_space": ["Random", 12, "discrete", SpaceTypes.BOX],
    "continue_game": [1.3, "string"],
    "tower": [5],
    "role": [["P1", "P2"], [5, 4], ["P1P2", "Random"], ["Random", "Random"]],
    "characters": [["Random", "TBD"], ["NoName", None]],
    "super_art": ["Random", 4, 0],
    "fighting_style": [False, 6, 0, "Random"],
    "ultimate_style": [(10, 0, 0), "string", (None, None, None), ("Random", "Random", "Random")],
}

def pytest_generate_tests(metafunc):
    test_vars, values_list = generate_pytest_decorator_input(gym_settings_var_order, ok_test_parameters, ko_test_parameters)
    metafunc.parametrize(test_vars, values_list)

# Gym
@pytest.mark.parametrize("game_id", list(games_dict.keys()))
@pytest.mark.parametrize("n_players", [1, 2])
def test_gym_settings(game_id, n_players, frame_shape, step_ratio, action_space, difficulty, continue_game,
                      tower, role, characters, super_art, fighting_style, ultimate_style, expected, mocker):

    game_data = games_dict[game_id]

    outfits_range = range(game_data["outfits"][0], game_data["outfits"][1] + 1)
    characters = [random.choice(game_data["char_list"]) if characters[idx] == "TBD" else characters[idx] for idx in range(2)]
    outfits = random.choice(outfits_range)

    # Env settings
    if (n_players == 1):
        settings = EnvironmentSettings()
    else:
        settings = EnvironmentSettingsMultiAgent()
    settings.game_id = game_id
    settings.frame_shape = frame_shape
    settings.step_ratio = step_ratio
    settings.action_space = (action_space, action_space)

    settings.difficulty = difficulty
    settings.continue_game = continue_game
    settings.tower = tower

    settings.role = (role[0], role[1])
    settings.characters = (characters[0], characters[1])
    settings.outfits = (outfits, outfits)
    settings.super_art = (super_art, super_art)
    settings.fighting_style = (fighting_style, fighting_style)
    settings.ultimate_style = (ultimate_style, ultimate_style)

    if n_players != 2:
        for key in ["action_space", "role", "characters" , "outfits",
                    "super_art", "fighting_style", "ultimate_style"]:
            setattr(settings, key, getattr(settings, key)[0])

    assert func(settings, mocker) == expected
