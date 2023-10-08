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

def func(game_id, n_players, wrappers_settings, use_mocker, mocker):
    if use_mocker is True:
        load_mocker(mocker)
    try:
        # Settings
        if (n_players == 1):
            settings = EnvironmentSettings()
        else:
            settings = EnvironmentSettingsMultiAgent()

        settings.step_ratio = 1
        settings.frame_shape = (128, 128, 1)

        env = diambra.arena.make(game_id, settings, wrappers_settings)
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
        warnings.warn(UserWarning("Average speed = {} FPS, STD {} FPS".format(avg_fps, np.std(fps_val2))))

        return 0
    except Exception as e:
        print(e)
        return 1

n_players = [1, 2]
game_ids = ["doapp", "sfiii3n", "tektagt", "umk3", "samsh5sp", "kof98umh"]

@pytest.mark.parametrize("n_players", n_players)
def test_speed_gym_mock(n_players, mocker):
    use_mocker = True
    game_id = "doapp"
    assert func(game_id, n_players, WrappersSettings(), use_mocker, mocker) == 0

@pytest.mark.parametrize("n_players", n_players)
def test_speed_wrappers_mock(n_players, mocker):
    use_mocker = True
    game_id = "doapp"

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

    assert func(game_id, n_players, wrappers_settings, use_mocker, mocker) == 0

@pytest.mark.parametrize("game_id", game_ids)
@pytest.mark.parametrize("n_players", n_players)
def test_speed_gym_integration(game_id, n_players, mocker):
    use_mocker = False
    assert func(game_id, n_players, WrappersSettings(), use_mocker, mocker) == 0