#!/usr/bin/env python3
import pytest
import sys
import random
from os.path import expanduser
import os
from engine_mock import DiambraEngineMock, EngineMockParams

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

def func(player, continue_game, action_space, attack_buttons_combination,
         wrappers_settings, traj_rec_settings, mocker):

    diambra_engine_mock_params = EngineMockParams()
    diambra_engine_mock = DiambraEngineMock(diambra_engine_mock_params)

    mocker.patch('diambra.arena.engine.interface.DiambraEngine.__init__', diambra_engine_mock._mock__init__)
    mocker.patch('diambra.arena.engine.interface.DiambraEngine._env_init', diambra_engine_mock._mock_env_init)
    mocker.patch('diambra.arena.engine.interface.DiambraEngine._reset', diambra_engine_mock._mock_reset)
    mocker.patch('diambra.arena.engine.interface.DiambraEngine._step_1p', diambra_engine_mock._mock_step_1p)
    mocker.patch('diambra.arena.engine.interface.DiambraEngine._step_2p', diambra_engine_mock._mock_step_2p)
    mocker.patch('diambra.arena.engine.interface.DiambraEngine.close', diambra_engine_mock._mock_close)

    try:
        # Settings
        settings = {}
        settings["game_id"] = "mock"
        settings["player"] = player
        settings["continue_game"] = continue_game
        settings["action_space"] = [action_space, action_space]
        settings["attack_but_combination"] = [attack_buttons_combination, attack_buttons_combination]
        if settings["player"] != "P1P2":
            settings["action_space"] = settings["action_space"][0]
            settings["attack_but_combination"] = settings["attack_but_combination"][0]

        return env_exec(settings, wrappers_settings, traj_rec_settings)

        return 0
    except Exception as e:
        print(e)
        return 1


'''
    # System level
    step_ratio: int = 6

    # Game level
    game_id: str = "doapp"
    player: str = "Random"
    continue_game: float = 0.0
    difficulty: int = 3
    frame_shape: Tuple[int, int, int] = (0, 0, 0)

    tower: int = 3  # UMK3 Specific

    # Player level
    characters: Union[str, Tuple[str], Tuple[str, str], Tuple[str, str, str]] = ("Random", "Random", "Random")
    char_outfits: int = 2
    action_space: str = "multi_discrete"
    attack_but_combination: bool = True

    super_art: int = 0  # SFIII Specific

    fighting_style: int = 0 # KOF Specific
    ultimate_style: Tuple[int, int, int] = (0, 0, 0) # KOF Specific
'''

continue_games = [-1.0, 0.0, 0.3]
action_spaces = ["discrete", "multi_discrete"]
attack_buttons_combinations = [False, True]

# Gym
@pytest.mark.parametrize("continue_game", continue_games)
@pytest.mark.parametrize("action_space", action_spaces)
@pytest.mark.parametrize("attack_buttons_combination", attack_buttons_combinations)
def test_settings_gym_1p_ok(continue_game, action_space, attack_buttons_combination, mocker):
    wrappers_settings = {}
    traj_rec_settings = {}
    assert func("Random", continue_game, action_space, attack_buttons_combination,
                wrappers_settings, traj_rec_settings, mocker) == 0


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
