#!/usr/bin/env python3
from diambra.arena.arena_imitation_learning_gym import ImitationLearning
from diambra.arena.utils.gym_utils import show_wrap_obs
import argparse
import os
from os import listdir
import numpy as np

try:
    parser = argparse.ArgumentParser()
    parser.add_argument('--path',     type=str, required=True,
                        help='Path where recorded files are stored')
    parser.add_argument('--nProc',    type=int, default=1,
                        help='Number of processors [(1), 2]')
    parser.add_argument('--hardcore', type=int, default=0,
                        help='Hard Core Mode [(0=False), 1=True]')
    parser.add_argument('--viz',      type=int, default=0,
                        help='Visualization [(0=False), 1=True]')
    parser.add_argument('--waitKey',  type=int, default=1,
                        help='CV2 WaitKey [0, 1]')
    opt = parser.parse_args()
    print(opt)

    viz_flag = True if opt.viz == 1 else False

    # Show files in folder
    traj_rec_folder = opt.path
    trajectories_files = [os.path.join(traj_rec_folder, f) for f in listdir(
        traj_rec_folder) if os.path.isfile(os.path.join(traj_rec_folder, f))]
    print(trajectories_files)

    diambra_il_settings = {}
    diambra_il_settings["traj_files_list"] = trajectories_files
    diambra_il_settings["total_cpus"] = opt.nProc

    if opt.hardcore == 0:
        env = ImitationLearning(**diambra_il_settings)
    else:
        env = ImitationLearning(**diambra_il_settings)

    observation = env.reset()
    env.render(mode="human")

    env.traj_summary()

    show_wrap_obs(observation, env.n_actions_stack,
                  env.char_names, opt.waitKey, viz_flag)

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
        show_wrap_obs(observation, env.n_actions_stack,
                      env.char_names, opt.waitKey, viz_flag)

        print("----------")

        # if done:
        #    observation = info[procIdx]["terminal_observation"]

        cumulative_ep_rew += reward

        if (np.any([info["round_done"], info["stage_done"], info["game_done"]])
                and not done):
            # Frames equality check
            if opt.hardcore == 0:
                for frame_idx in range(observation["frame"].shape[2]-1):
                    if np.any(observation["frame"][:, :, frame_idx] != observation["frame"][:, :, frame_idx+1]):
                        raise RuntimeError("Frames inside observation after "
                                           "round/stage/game/episode done are "
                                           "not equal. Dones =",
                                           info["round_done"],
                                           info["stage_done"],
                                           info["game_done"],
                                           info["ep_done"])
            else:
                for frame_idx in range(observation.shape[2]-1):
                    if np.any(observation[:, :, frame_idx] != observation[:, :, frame_idx+1]):
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
            show_wrap_obs(observation, env.n_actions_stack,
                          env.char_names, opt.waitKey, viz_flag)

    if diambra_il_settings["total_cpus"] == 1:
        print("All ep. rewards =", cumulative_ep_rew_all)
        print("Mean cumulative reward =", np.mean(cumulative_ep_rew_all))
        print("Std cumulative reward =", np.std(cumulative_ep_rew_all))

    env.close()

    print("ALL GOOD!")
except Exception as e:
    print(e)
    print("ALL BAD")
