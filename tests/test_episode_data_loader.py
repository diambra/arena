#!/usr/bin/env python3
from diambra.arena.utils.diambra_data_loader import DiambraDataLoader
import os
from os.path import expanduser

def func():
    try:
        home_dir = expanduser("~")
        dataset_path = os.path.join(home_dir, "DIAMBRA/episode_recording/mock")

        data_loader = DiambraDataLoader(dataset_path)

        n_loops = data_loader.reset()

        while n_loops == 0:
            observation, action, reward, terminated, truncated, info = data_loader.step()
            print("Observation: {}".format(observation))
            print("Action: {}".format(action))
            print("Reward: {}".format(reward))
            print("Terminated: {}".format(terminated))
            print("Truncated: {}".format(truncated))
            print("Info: {}".format(info))
            data_loader.render()

            if terminated or truncated:
                n_loops = data_loader.reset()

        return 0
    except Exception as e:
        print(e)
        return 1

def test_episode_data_loader():
    assert func() == 0

