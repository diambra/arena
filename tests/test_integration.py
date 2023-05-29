#!/usr/bin/env python3
import pytest
from env_exec_interface import env_exec
import random
from os.path import expanduser
import os

# Example Usage:
# pytest
# (optional)
#    module.py (Run specific module)
#    -s (show output)
#    -k "expression" (filter tests using case-insensitive with parts of the test name and/or parameters values combined with boolean operators, e.g. "wrappers and doapp")

def func(game_id, player, continue_game, action_space, attack_buttons_combination,
         wrappers_settings, traj_rec_settings, hardcore_prob, no_action_prob):

    # Args
    args = {}
    args["interactive_viz"] = False
    args["n_episodes"] = 1

    args["no_action"] = random.choices([True, False], [no_action_probability, 1.0 - no_action_probability])[0]

    try:
        # Settings
        settings = {}
        settings["game_id"] = game_id
        settings["player"] = player
        settings["continue_game"] = continue_game
        settings["action_space"] = (action_space, action_space)
        settings["attack_but_combination"] = (attack_buttons_combination, attack_buttons_combination)
        if settings["player"] != "P1P2":
            settings["action_space"] = settings["action_space"][0]
            settings["attack_but_combination"] = settings["attack_but_combination"][0]
        settings["hardcore"] = random.choices([True, False], [hardcore_probability, 1.0 - hardcore_probability])[0]

        return env_exec(settings, wrappers_settings, traj_rec_settings, args)
    except Exception as e:
        print(e)
        return 1

game_ids = ["doapp", "sfiii3n", "tektagt", "umk3", "samsh5sp", "kof98umh"]
players = ["Random", "P1P2"]
action_spaces = ["multi_discrete"]
attack_buttons_combinations = [True]
continue_games = [-1.0, 0.3]
hardcore_probability = 0.4
no_action_probability = 0.5
rec_traj_probability = 0.5

@pytest.mark.parametrize("game_id", game_ids)
@pytest.mark.parametrize("player", players)
@pytest.mark.parametrize("continue_game", continue_games)
@pytest.mark.parametrize("action_space", action_spaces)
@pytest.mark.parametrize("attack_buttons_combination", attack_buttons_combinations)
def test_integration_gym(game_id, player, continue_game, action_space, attack_buttons_combination):
    wrappers_settings = {}
    traj_rec_settings = {}
    assert func(game_id, player, continue_game, action_space, attack_buttons_combination,
                wrappers_settings, traj_rec_settings, hardcore_probability, no_action_probability) == 0

@pytest.mark.parametrize("game_id", game_ids)
@pytest.mark.parametrize("player", players)
@pytest.mark.parametrize("continue_game", continue_games)
@pytest.mark.parametrize("action_space", action_spaces)
@pytest.mark.parametrize("attack_buttons_combination", attack_buttons_combinations)
def test_integration_wrappers(game_id, player, continue_game, action_space, attack_buttons_combination):

    # Env wrappers settings
    wrappers_settings = {}
    wrappers_settings["no_op_max"] = 0
    wrappers_settings["sticky_actions"] = 1
    wrappers_settings["hwc_obs_resize"] = (128, 128, 1)
    wrappers_settings["reward_normalization"] = True
    wrappers_settings["clip_rewards"] = False
    wrappers_settings["frame_stack"] = 4
    wrappers_settings["dilation"] = 1
    wrappers_settings["actions_stack"] = 12
    wrappers_settings["scale"] = True
    wrappers_settings["scale_mod"] = 0
    wrappers_settings["flatten"] = True
    if game_id != "tektagt":
        wrappers_settings["filter_keys"] = ["stage", "P1_ownSide", "P1_oppSide", "P1_oppSide",
                                            "P1_ownHealth", "P1_oppHealth", "P1_oppChar",
                                            "P1_actions_move", "P1_actions_attack"]
    else:
        wrappers_settings["filter_keys"] = ["stage", "P1_ownSide", "P1_oppSide", "P1_oppSide",
                                            "P1_ownHealth1", "P1_oppHealth1", "P1_oppChar",
                                            "P1_ownHealth2", "P1_oppHealth2",
                                            "P1_actions_move", "P1_actions_attack"]

    # Recording settings
    home_dir = expanduser("~")
    traj_rec_settings = {}
    traj_rec_settings["username"] = "Alex"
    traj_rec_settings["file_path"] = os.path.join(expanduser("~"), "DIAMBRA/trajRecordings", game_id)
    traj_rec_settings["ignore_p2"] = False

    if (random.choices([True, False], [rec_traj_probability, 1.0 - rec_traj_probability])[0] is False):
        traj_rec_settings = {}
    else:
        wrappers_settings["flatten"] = False

    assert func(game_id, player, continue_game, action_space, attack_buttons_combination,
                wrappers_settings, traj_rec_settings, hardcore_probability, no_action_probability) == 0
