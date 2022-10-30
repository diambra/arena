#!/usr/bin/env python3
import pytest
import sys
import time
import random
from os.path import expanduser
import os
import diambra.arena
import argparse
import numpy as np

def reject_outliers(data):
    u = np.mean(data)
    s = np.std(data)
    filtered = [e for e in data if (u - 2 * s < e < u + 2 * s)]
    return filtered

def func(game_id, player, wrappers_settings, target_speed):

    try:
        # Settings
        settings = {}
        settings["player"] = player
        settings["step_ratio"] = 1
        settings["frame_shape"] = [128, 128, 1]
        settings["action_space"] = "discrete"
        settings["attack_but_combination"] = False

        env = diambra.arena.make(game_id, settings, wrappers_settings)

        observation = env.reset()
        n_step = 0

        fps_val = []

        while n_step < 1000:

            n_step += 1
            actions = [None, None]
            if settings["player"] != "P1P2":
                actions = env.action_space.sample()
            else:
                for idx in range(2):
                    actions[idx] = env.action_space["P{}".format(idx + 1)].sample()

            if (settings["player"] == "P1P2" or settings["action_space"] != "discrete"):
                actions = np.append(actions[0], actions[1])

            tic = time.time()
            observation, reward, done, info = env.step(actions)
            toc = time.time()
            fps = 1 / (toc - tic)
            fps_val.append(fps)

            if done:
                observation = env.reset()
                break

        env.close()

        fps_val2 = reject_outliers(fps_val)
        avg_fps = np.mean(fps_val2)
        print("Average speed = {} FPS, STD {} FPS".format(avg_fps, np.std(fps_val2)))

        if abs(avg_fps - target_speed) > target_speed * 0.025:
            raise RuntimeError("Fps different than expected: {} VS {}".format(avg_fps, target_speed))

        print("COMPLETED SUCCESSFULLY!")
        return 0
    except Exception as e:
        print(e)
        print("ERROR, ABORTED.")
        return 1

game_ids = ["doapp", "sfiii3n", "tektagt", "umk3", "samsh5sp", "kof98umh"]
players = ["Random", "P1P2"]

target_speeds = {}
target_speeds["doapp"] = [696, 1256]
target_speeds["sfiii3n"] = [1090, 916]
target_speeds["tektagt"] = [2500, 2500]
target_speeds["umk3"] = [969, 1213]
target_speeds["samsh5sp"] = [1339, 1123]
target_speeds["kof98umh"] = [1786, 3987]

@pytest.mark.parametrize("game_id", game_ids)
@pytest.mark.parametrize("player", players)
def test_speed_gym(game_id, player):
    wrappers_settings = {}
    assert func(game_id, player, wrappers_settings, target_speeds[game_id][0]) == 0

@pytest.mark.parametrize("game_id", game_ids)
@pytest.mark.parametrize("player", players)
def test_speed_wrappers(game_id, player):

    # Env wrappers settings
    wrappers_settings = {}
    wrappers_settings["no_op_max"] = 0
    wrappers_settings["sticky_actions"] = 1
    wrappers_settings["reward_normalization"] = True
    wrappers_settings["clip_rewards"] = False
    wrappers_settings["frame_stack"] = 4
    wrappers_settings["dilation"] = 1
    wrappers_settings["actions_stack"] = 12
    wrappers_settings["scale"] = True
    wrappers_settings["scale_mod"] = 0
    if game_id != "tektagt":
        wrappers_settings["filter_keys"] = ["stage", "P1_ownSide", "P1_oppSide", "P1_oppSide",
                                            "P1_ownHealth", "P1_oppHealth", "P1_oppChar",
                                            "P1_actions_move", "P1_actions_attack"]
    else:
        wrappers_settings["filter_keys"] = ["stage", "P1_ownSide", "P1_oppSide", "P1_oppSide",
                                            "P1_ownHealth1", "P1_oppHealth1", "P1_oppChar",
                                            "P1_ownHealth2", "P1_oppHealth2",
                                            "P1_actions_move", "P1_actions_attack"]

    assert func(game_id, player, wrappers_settings, target_speeds[game_id][1]) == 0
