#!/usr/bin/env python3
import pytest
import sys
import random
from os.path import expanduser
import os
from engine_mock import DiambraEngineMock, EngineMockParams
from diambra.arena.utils.gym_utils import available_games

# Example Usage:
# pytest
# (optional)
#    module.py (Run specific module)
#    -s (show output)
#    -k 'expression' (filter tests using case-insensitive with parts of the test name and/or parameters values combined with boolean operators, e.g. 'wrappers and doapp')

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

    diambra_engine_mock_params = EngineMockParams()
    diambra_engine_mock = DiambraEngineMock(diambra_engine_mock_params)

    mocker.patch('diambra.arena.engine.interface.DiambraEngine.__init__', diambra_engine_mock._mock__init__)
    mocker.patch('diambra.arena.engine.interface.DiambraEngine._env_init', diambra_engine_mock._mock_env_init)
    mocker.patch('diambra.arena.engine.interface.DiambraEngine._reset', diambra_engine_mock._mock_reset)
    mocker.patch('diambra.arena.engine.interface.DiambraEngine._step_1p', diambra_engine_mock._mock_step_1p)
    mocker.patch('diambra.arena.engine.interface.DiambraEngine._step_2p', diambra_engine_mock._mock_step_2p)
    mocker.patch('diambra.arena.engine.interface.DiambraEngine.close', diambra_engine_mock._mock_close)

    try:
        return env_exec(settings, wrappers_settings, traj_rec_settings)

        return 0
    except Exception as e:
        print(e)
        return 1

games_dict = available_games(False)

continue_games = [-1.0, 0.0, 0.3]
action_spaces = ["discrete", "multi_discrete"]
attack_buttons_combinations = [False, True]
game_ids = game_dict.keys()
players = ["P1", "P2", "Random", "P1P2"]
step_ratios = [1, 3, 6]
frame_shapes = [(0, 0, 0), (0, 0, 1), (0, 0, 3), (82, 82, 0), (82, 82, 1), (82, 82, 3)]
towers = [1, 3, 4]
super_arts = [0, 1, 3]
fighting_styles = [0, 1, 3]
ultimate_styles = [0, 1, 2]

# Gym
@pytest.mark.parametrize("game_id", game_ids)
@pytest.mark.parametrize("player", players)
@pytest.mark.parametrize("step_ratio", step_ratios)
@pytest.mark.parametrize("frame_shape", frame_shapes)
@pytest.mark.parametrize("tower", towers)
@pytest.mark.parametrize("super_art", super_arts)
@pytest.mark.parametrize("fighting_style", fighting_styles)
@pytest.mark.parametrize("ultimate_style", ultimate_styles)
@pytest.mark.parametrize("continue_game", continue_games)
@pytest.mark.parametrize("action_space", action_spaces)
@pytest.mark.parametrize("attack_buttons_combination", attack_buttons_combinations)
def test_settings_gym_1p_ok(game_id, player, step_ratio, frame_shape, tower, super_art,
                            fighting_style, ultimate_style, continue_game, action_space,
                            attack_buttons_combination, mocker):

    difficulty_range = range(games_dict[game_id]["difficulty"][0], games_dict[game_id]["difficulty"][1]+1)
    difficulty = random.choice(difficulty_range)
    characters =
    char_outfits =

    # Env settings
    settings = {}
    settings["game_id"] = game_id
    settings["player"] = player
    settings["step_ratio"] = step_ratio
    settings["continue_game"] = continue_game
    settings["difficulty"] = difficulty
    settings["frame_shape"] = frame_shape

    settings["tower"] = tower

    settings["characters"] = [characters, characters]
    settings["char_outfits"] = [char_outfits, char_outfits]
    settings["action_space"] = [action_space, action_space]
    settings["attack_but_combination"] = [attack_buttons_combination, attack_buttons_combination]

    settings["super_art"] = [super_art, super_art]
    settings["fighting_style"] = [fighting_style, fighting_style]
    settings["ultimate_style"] = [ultimate_style, ultimate_style]

    if settings["player"] != "P1P2":
        for key in ["characters" , "char_outfits", "action_space", "attack_but_combination",
                    "super_art", "fighting_style", "ultimate_style"]:
            settings[key] = settings[key][0]

    wrappers_settings = {}
    traj_rec_settings = {}

    assert func(settings, wrappers_settings, traj_rec_settings, mocker) == 0


# Wrappers
@pytest.mark.parametrize("player", players)
@pytest.mark.parametrize("continue_game", continue_games)
@pytest.mark.parametrize("action_space", action_spaces)
@pytest.mark.parametrize("attack_buttons_combination", attack_buttons_combinations)
def test_settings_wrappers_1p_ok(player, continue_game, action_space, attack_buttons_combination, mocker):

    # Env wrappers settings
    wrappers_settings = {}
    wrappers_settings["no_op_max"] = 0
    wrappers_settings["sticky_actions"] = 1
    wrappers_settings["hwc_obs_resize"] = [128, 128, 1]
    wrappers_settings["reward_normalization"] = True
    wrappers_settings["clip_rewards"] = False
    wrappers_settings["frame_stack"] = 4
    wrappers_settings["dilation"] = 1
    wrappers_settings["actions_stack"] = 12
    wrappers_settings["scale"] = True
    wrappers_settings["scale_mod"] = 0
    wrappers_settings["flatten"] = True
    wrappers_settings["filter_keys"] = ["stage", "P1_ownSide", "P1_oppSide", "P1_oppSide",
                                        "P1_oppChar", "P1_actions_move", "P1_actions_attack"]

    # Recording settings
    home_dir = expanduser("~")
    traj_rec_settings = {}
    traj_rec_settings["user_name"] = "Alex"
    traj_rec_settings["file_path"] = os.path.join(home_dir, "DIAMBRA/trajRecordings/mock")
    traj_rec_settings["ignore_p2"] = 0
    traj_rec_settings["commit_hash"] = "0000000"

    if (random.choices([True, False], [rec_traj_probability, 1.0 - rec_traj_probability])[0] is False):
        traj_rec_settings = {}

    assert func(player, continue_game, action_space, attack_buttons_combination,
                wrappers_settings, traj_rec_settings, hardcore_probability, no_action_probability, mocker) == 0
