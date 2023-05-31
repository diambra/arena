#!/usr/bin/env python3
import pytest
from env_exec_interface import env_exec
import time
from os.path import expanduser
import diambra.arena
from diambra.arena.utils.engine_mock import DiambraEngineMock
import numpy as np
import warnings

def reject_outliers(data):
    u = np.mean(data)
    s = np.std(data)
    filtered = [e for e in data if (u - 2 * s < e < u + 2 * s)]
    return filtered

def func(player, wrappers_settings, target_speed, mocker):

    diambra_engine_mock = DiambraEngineMock(fps=500)

    mocker.patch("diambra.arena.engine.interface.DiambraEngine.__init__", diambra_engine_mock._mock__init__)
    mocker.patch("diambra.arena.engine.interface.DiambraEngine._env_init", diambra_engine_mock._mock_env_init)
    mocker.patch("diambra.arena.engine.interface.DiambraEngine._reset", diambra_engine_mock._mock_reset)
    mocker.patch("diambra.arena.engine.interface.DiambraEngine._step_1p", diambra_engine_mock._mock_step_1p)
    mocker.patch("diambra.arena.engine.interface.DiambraEngine._step_2p", diambra_engine_mock._mock_step_2p)
    mocker.patch("diambra.arena.engine.interface.DiambraEngine.close", diambra_engine_mock._mock_close)

    try:
        # Settings
        settings = {}
        settings["player"] = player
        settings["action_space"] = "discrete"
        settings["attack_but_combination"] = False
        if player == "P1P2":
            settings["action_space"] = ("discrete", "discrete")
            settings["attack_but_combination"] = (False, False)

        env = diambra.arena.make("doapp", settings, wrappers_settings)

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
            # TODO: restore when using a stable platform for testing with consistent measurement
            #if avg_fps < target_speed:
            #    raise RuntimeError("Fps lower than expected: {} VS {}".format(avg_fps, target_speed))
            #else:
            #    warnings.warn(UserWarning("Fps higher than expected: {} VS {}".format(avg_fps, target_speed)))
            warnings.warn(UserWarning("Fps different than expected: {} VS {}".format(avg_fps, target_speed)))

        return 0
    except Exception as e:
        print(e)
        return 1

players = ["Random", "P1P2"]

target_speeds = [400, 300]

@pytest.mark.parametrize("player", players)
def test_speed_gym(player, mocker):
    wrappers_settings = {}
    assert func(player, wrappers_settings, target_speeds[0], mocker) == 0

@pytest.mark.parametrize("player", players)
def test_speed_wrappers(player, mocker):

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
    wrappers_settings["flatten"] = True
    wrappers_settings["filter_keys"] = ["stage", "P1_ownSide", "P1_oppSide", "P1_oppSide",
                                        "P1_ownHealth", "P1_oppHealth", "P1_oppChar",
                                        "P1_actions_move", "P1_actions_attack"]

    assert func(player, wrappers_settings, target_speeds[1], mocker) == 0
