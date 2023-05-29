#!/usr/bin/env python3
import pytest
import diambra.arena
import os
from os import listdir
import numpy as np

def func(path, hardcore):
    try:
        nProc = 1

        # Show files in folder
        traj_rec_folder = path
        trajectories_files = [os.path.join(traj_rec_folder, f) for f in listdir(
            traj_rec_folder) if os.path.isfile(os.path.join(traj_rec_folder, f))]
        print(trajectories_files)

        diambra_il_settings = {}
        diambra_il_settings["traj_files_list"] = trajectories_files
        diambra_il_settings["total_cpus"] = nProc

        if hardcore is False:
            env = diambra.arena.ImitationLearning(**diambra_il_settings)
        else:
            env = diambra.arena.ImitationLearningHardcore(**diambra_il_settings)

        observation = env.reset()
        env.render(mode="human")

        env.traj_summary()

        env.show_obs(observation)

        cumulative_ep_rew = 0.0
        cumulative_ep_rew_all = []

        max_num_ep = 10
        curr_num_ep = 0

        while curr_num_ep < max_num_ep:

            dummy_actions = 0
            observation, reward, done, info = env.step(dummy_actions)
            env.render(mode="human")

            action = info["action"]

            print("Action:", action)
            print("reward:", reward)
            print("done = ", done)
            for k, v in info.items():
                print("info[\"{}\"] = {}".format(k, v))
            env.show_obs(observation)

            print("----------")

            # if done:
            #    observation = info[procIdx]["terminal_observation"]

            cumulative_ep_rew += reward

            if (np.any([info["round_done"], info["stage_done"], info["game_done"]]) and not done):
                # Frames equality check
                if hardcore is False:
                    for frame_idx in range(observation["frame"].shape[2] - 1):
                        if np.any(observation["frame"][:, :, frame_idx] != observation["frame"][:, :, frame_idx + 1]):
                            raise RuntimeError("Frames inside observation after "
                                               "round/stage/game/episode done are "
                                               "not equal. Dones =",
                                               info["round_done"],
                                               info["stage_done"],
                                               info["game_done"],
                                               info["ep_done"])
                else:
                    for frame_idx in range(observation.shape[2] - 1):
                        if np.any(observation[:, :, frame_idx] != observation[:, :, frame_idx + 1]):
                            raise RuntimeError("Frames inside observation after "
                                               "round/stage/game/episode done are "
                                               "not equal. Dones =",
                                               info["round_done"],
                                               info["stage_done"],
                                               info["game_done"],
                                               info["ep_done"])

            if np.any(env.exhausted):
                break

            if done:
                curr_num_ep += 1
                print("Ep. # = ", curr_num_ep)
                print("Ep. Cumulative Rew # = ", cumulative_ep_rew)

                cumulative_ep_rew_all.append(cumulative_ep_rew)
                cumulative_ep_rew = 0.0

                observation = env.reset()
                env.render(mode="human")
                env.show_obs(observation)

        if diambra_il_settings["total_cpus"] == 1:
            print("All ep. rewards =", cumulative_ep_rew_all)
            print("Mean cumulative reward =", np.mean(cumulative_ep_rew_all))
            print("Std cumulative reward =", np.std(cumulative_ep_rew_all))

        env.close()

        return 0
    except Exception as e:
        print(e)
        return 1


base_path = os.path.dirname(__file__)
normal_discrete = os.path.join(base_path, "data/Discrete/Normal")
hardcore_discrete = os.path.join(base_path, "data/Discrete/HC")

normal_multi_discrete = os.path.join(base_path, "data/MultiDiscrete/Normal")
hardcore_multi_discrete = os.path.join(base_path, "data/MultiDiscrete/HC")

@pytest.mark.parametrize("path", [normal_discrete, normal_multi_discrete])
def test_imitation_normal_mode(path):
    assert func(path, False) == 0

@pytest.mark.parametrize("path", [hardcore_discrete, hardcore_multi_discrete])
def test_imitation_hardcore_mode(path):
    assert func(path, True) == 0

