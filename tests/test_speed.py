#!/usr/bin/env python3
import pytest
import time
import diambra.arena
from diambra.arena import EnvironmentSettings, EnvironmentSettingsMultiAgent, WrappersSettings
from diambra.arena.utils.engine_mock import load_mocker
import numpy as np
import warnings

def reject_outliers(data):
    u = np.mean(data)
    s = np.std(data)
    filtered = [e for e in data if (u - 2 * s < e < u + 2 * s)]
    return filtered

def func(n_players, wrappers_settings, target_speed, mocker):
    load_mocker(mocker)
    try:
        # Settings
        if (n_players == 1):
            settings = EnvironmentSettings()
        else:
            settings = EnvironmentSettingsMultiAgent()

        env = diambra.arena.make("doapp", settings, wrappers_settings)
        observation, info = env.reset()

        n_step = 0
        fps_val = []
        while n_step < 1000:
            n_step += 1
            actions = env.action_space.sample()

            tic = time.time()
            observation, reward, terminated, truncated, info = env.step(actions)
            toc = time.time()
            fps = 1 / (toc - tic)
            fps_val.append(fps)

            if terminated or truncated:
                observation, info = env.reset()
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

n_players = [1, 2]
target_speeds = [400, 300]

@pytest.mark.parametrize("n_players", n_players)
def test_speed_gym(n_players, mocker):
    assert func(n_players, WrappersSettings(), target_speeds[0], mocker) == 0

@pytest.mark.parametrize("n_players", n_players)
def test_speed_wrappers(n_players, mocker):

    # Env wrappers settings
    wrappers_settings = WrappersSettings()
    wrappers_settings.no_op_max = 0
    wrappers_settings.repeat_action = 1
    wrappers_settings.normalize_reward = True
    wrappers_settings.clip_reward = False
    wrappers_settings.stack_frames = 4
    wrappers_settings.dilation = 1
    wrappers_settings.add_last_action = True
    wrappers_settings.stack_actions = 12
    wrappers_settings.scale = True
    wrappers_settings.role_relative = True
    wrappers_settings.flatten = True

    suffix = ""
    if n_players == 2:
        suffix = "agent_0_"
    wrappers_settings.filter_keys = ["stage", "timer", suffix + "own_side", suffix + "opp_side",
                                     suffix + "opp_character", suffix + "action"]

    assert func(n_players, wrappers_settings, target_speeds[1], mocker) == 0
