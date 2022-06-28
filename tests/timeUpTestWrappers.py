#!/usr/bin/env python3
import diambra.arena
from diambra.arena.utils.gym_utils import env_spaces_summary, show_wrap_obs
import argparse
import time
from os.path import expanduser
import numpy as np

if __name__ == '__main__':
    time_dep_seed = int((time.time()-int(time.time()-0.5))*1000)

    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--gameId', type=str,
                            default="doapp", help='Game ID')
        parser.add_argument('--continueGame', type=float,
                            default=0.0, help='ContinueGame flag (-inf,+1.0]')
        parser.add_argument('--firstRoundAct', type=int, default=0,
                            help='Actions active for first round (0=F)')
        parser.add_argument('--interactiveViz', type=int, default=0,
                            help='Interactive Visualization (0=F)')
        parser.add_argument('--envAddress', type=str,
                            default="", help='diambraEngine Address')
        opt = parser.parse_args()
        print(opt)

        viz_flag = bool(opt.interactiveViz)
        wait_key = 1
        if viz_flag:
            wait_key = 0

        home_dir = expanduser("~")

        # Settings
        settings = {}
        if opt.envAddress != "":
            settings["env_address"] = opt.envAddress
        settings["player"] = "P1P2"
        settings["step_ratio"] = 3
        settings["frame_shape"] = [128, 128, 1]
        settings["continue_game"] = opt.continueGame
        settings["show_final"] = False

        settings["action_space"] = ["discrete", "discrete"]
        settings["attack_but_combination"] = [False, False]

        settings["hardcore"] = False

        traj_rec_settings = None

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

        env = diambra.arena.make(opt.gameId, settings, wrappers_settings,
                                 traj_rec_settings, seed=time_dep_seed)

        # Print environment obs and action spaces summary
        env_spaces_summary(env)

        observation = env.reset()

        while True:

            actions = [None, None]
            for idx in range(2):
                if (opt.firstRoundAct == 1
                    and observation["P1"]["ownWins"] == 0.0
                        and observation["P1"]["oppWins"] == 0.0):
                    actions[idx] = env.action_space["P{}".format(
                        idx+1)].sample()
                else:
                    actions[idx] = 0

            actions = np.append(actions[0], actions[1])

            observation, reward, done, info = env.step(actions)

            print("action =", actions)
            print("reward =", reward)
            print("done =", done)
            for k, v in info.items():
                print("info[\"{}\"] = {}".format(k, v))
            show_wrap_obs(
                observation, wrappers_settings["actions_stack"],
                env.char_names, wait_key, viz_flag)
            print("----------")

            if done:
                print("Resetting Env")
                observation = env.reset()
                show_wrap_obs(
                    observation, wrappers_settings["actions_stack"],
                    env.char_names, wait_key, viz_flag)
                break

        env.close()

        print("ALL GOOD!")
    except Exception as e:
        print(e)
        print("ALL BAD")
