import sys
import os
import time
import numpy as np
import argparse
base_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(base_path, '../'))
from diambra.arena.utils.gym_utils import discrete_to_multi_discrete_action
from sb_utils import show_obs
from make_sb_env import make_sb_env
from wrappers.tektag_rew_wrap import TektagRoundEndChar2Penalty,\
                                     TektagHealthBarUnbalancePenalty


if __name__ == '__main__':
    time_dep_seed = int((time.time()-int(time.time()-0.5))*1000)

    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--gameId',         type=str,   default="doapp",    help='Game ID')
        parser.add_argument('--player',         type=str,   default="Random",   help='Player [(Random), P1, P2, P1P2]')
        parser.add_argument('--character1',     type=str,   default="Random",   help='Character P1 (Random)')
        parser.add_argument('--character2',     type=str,   default="Random",   help='Character P2 (Random)')
        parser.add_argument('--character1_2',   type=str,   default="Random",   help='Character P1_2 (Random)')
        parser.add_argument('--character2_2',   type=str,   default="Random",   help='Character P2_2 (Random)')
        parser.add_argument('--character1_3',   type=str,   default="Random",   help='Character P1_3 (Random)')
        parser.add_argument('--character2_3',   type=str,   default="Random",   help='Character P2_3 (Random)')
        parser.add_argument('--stepRatio',      type=int,   default=6,          help='Frame ratio')
        parser.add_argument('--nEpisodes',      type=int,   default=1,          help='Number of episodes')
        parser.add_argument('--continueGame',   type=float, default=0.0,        help='ContinueGame flag (-inf,+1.0]')
        parser.add_argument('--actionSpace',    type=str,   default="discrete", help='(discrete)/multi_discrete')
        parser.add_argument('--attButComb',     type=int,   default=0,          help='If to use attack button combinations (0=False)/1=True')
        parser.add_argument('--noAction',       type=int,   default=0,          help='If to use no action policy (0=False)')
        parser.add_argument('--hardcore',       type=int,   default=0,          help='Hard core mode (0=False)')
        parser.add_argument('--interactiveViz', type=int,   default=0,          help='Interactive Visualization (0=False)')
        opt = parser.parse_args()
        print(opt)

        viz_flag = bool(opt.interactiveViz)
        wait_key = 1
        if viz_flag:
            wait_key = 0

        # Environment settings
        settings = {}
        settings["game_id"] = opt.gameId
        settings["continue_game"] = opt.continueGame
        settings["step_ratio"] = opt.stepRatio
        settings["frame_shape"] = [128, 128, 1]
        settings["player"] = opt.player

        settings["characters"] = [[opt.character1, opt.character1_2, opt.character1_3],
                                  [opt.character2, opt.character2_2, opt.character2_3]]
        settings["char_outfits"] = [2, 2]

        settings["action_space"] = [opt.actionSpace, opt.actionSpace]
        settings["attack_but_combination"] = [opt.attButComb, opt.attButComb]
        if settings["player"] != "P1P2":
            settings["action_space"] = settings["action_space"][0]
            settings["attack_but_combination"] = settings["attack_but_combination"][0]

        idx_list = [0, 1]
        if settings["player"] != "P1P2":
            idx_list = [0]

        # Wrappers settings
        wrappers_settings = {}
        wrappers_settings["no_op_max"] = 0
        wrappers_settings["reward_normalization"] = True
        wrappers_settings["clip_rewards"] = False
        wrappers_settings["frame_stack"] = 4
        wrappers_settings["dilation"] = 1
        wrappers_settings["actions_stack"] = 12
        wrappers_settings["scale"] = True
        wrappers_settings["scale_mod"] = 0

        # Additional custom wrappers
        custom_wrappers = None
        if opt.gameId == "tektagt" and settings["player"] != "P1P2":
            custom_wrappers = [TektagRoundEndChar2Penalty, TektagHealthBarUnbalancePenalty]

        # Additional obs key list
        key_to_add = []
        key_to_add.append("actions")

        if opt.gameId != "tektagt":
            key_to_add.append("ownHealth")
            key_to_add.append("oppHealth")
        else:
            key_to_add.append("ownHealth1")
            key_to_add.append("ownHealth2")
            key_to_add.append("oppHealth1")
            key_to_add.append("oppHealth2")
            key_to_add.append("ownActiveChar")
            key_to_add.append("oppActiveChar")

        key_to_add.append("ownSide")
        key_to_add.append("oppSide")
        if settings["player"] != "P1P2":
            key_to_add.append("stage")

        key_to_add.append("ownChar")
        key_to_add.append("oppChar")

        n_rounds = 2
        if opt.gameId == "kof98umh":
            n_rounds = 3

        hardcore = False if opt.hardcore == 0 else True
        settings["hardcore"] = hardcore

        env, _ = make_sb_env(time_dep_seed, settings, wrappers_settings,
                             custom_wrappers=custom_wrappers,
                             key_to_add=key_to_add, no_vec=True)

        print("Observation Space:", env.observation_space)
        print("Action Space:", env.action_space)

        if not hardcore:
            print("Keys to Dict:")
            for k, v in env.keys_to_dict.items():
                print(k, v)

        n_actions = env.n_actions

        actions_print_dict = env.print_actions_dict

        observation = env.reset()

        show_obs(observation, key_to_add, env.key_to_add_count, wrappers_settings["actions_stack"],
                 n_actions, wait_key, viz_flag, env.char_names, hardcore, idx_list)

        cumulative_ep_rew = 0.0
        cumulative_ep_rew_all = []

        max_num_ep = opt.nEpisodes
        curr_num_ep = 0

        while curr_num_ep < max_num_ep:

            actions = [None, None]
            if settings["player"] != "P1P2":
                actions = env.action_space.sample()

                if opt.noAction == 1:
                    if settings["action_space"] == "multi_discrete":
                        for iEl, _ in enumerate(actions):
                            actions[iEl] = 0
                    else:
                        actions = 0

                if settings["action_space"] == "discrete":
                    move_action, att_action = discrete_to_multi_discrete_action(actions, env.n_actions[0][0])
                else:
                    move_action, att_action = actions[0], actions[1]

                print("(P1) {} {}".format(actions_print_dict[0][move_action],
                                          actions_print_dict[1][att_action]))

            else:
                for idx in range(2):
                    actions[idx] = env.action_space["P{}".format(idx+1)].sample()

                    if opt.noAction == 1 and idx == 0:
                        if settings["action_space"][idx] == "multi_discrete":
                            for iEl, _ in enumerate(actions[idx]):
                                actions[idx][iEl] = 0
                        else:
                            actions[idx] = 0

                    if settings["action_space"][idx] == "discrete":
                        move_action, att_action = discrete_to_multi_discrete_action(actions[idx], env.n_actions[idx][0])
                    else:
                        move_action, att_action = actions[idx][0], actions[idx][1]

                    print("(P{}) {} {}".format(idx+1, actions_print_dict[0][move_action],
                                               actions_print_dict[1][att_action]))

            if settings["player"] == "P1P2" or settings["action_space"] != "discrete":
                actions = np.append(actions[0], actions[1])

            observation, reward, done, info = env.step(actions)

            cumulative_ep_rew += reward
            print("action =", actions)
            print("reward =", reward)
            print("done =", done)
            for k, v in info.items():
                print("info[\"{}\"] = {}".format(k, v))
            show_obs(observation, key_to_add, env.key_to_add_count, wrappers_settings["actions_stack"], n_actions,
                     wait_key, viz_flag, env.char_names, hardcore, idx_list)
            print("--")
            print("Current Cumulative Reward =", cumulative_ep_rew)

            print("----------")

            if done:
                print("Resetting Env")
                curr_num_ep += 1
                print("Ep. # = ", curr_num_ep)
                print("Ep. Cumulative Rew # = ", cumulative_ep_rew)
                cumulative_ep_rew_all.append(cumulative_ep_rew)
                cumulative_ep_rew = 0.0

                observation = env.reset()
                show_obs(observation, key_to_add, env.key_to_add_count,
                         wrappers_settings["actions_stack"], n_actions,
                         wait_key, viz_flag, env.char_names, hardcore, idx_list)

        print("Cumulative reward = ", cumulative_ep_rew_all)
        print("Mean cumulative reward = ", np.mean(cumulative_ep_rew_all))
        print("Std cumulative reward = ", np.std(cumulative_ep_rew_all))

        env.close()

        if len(cumulative_ep_rew_all) != max_num_ep:
            raise RuntimeError("Not run all episodes")

        if opt.continueGame <= 0.0:
            max_continue = int(-opt.continueGame)
        else:
            max_continue = 0

        if opt.gameId == "tektagt":
            max_continue = (max_continue + 1) * 0.7 - 1

        if opt.noAction == 1 and np.mean(cumulative_ep_rew_all) > -(max_continue+1)*2*n_rounds+0.001:
            raise RuntimeError("NoAction policy and average reward different than {} ({})".format(-(max_continue+1)*2*n_rounds, np.mean(cumulative_ep_rew_all)))

        print("COMPLETED SUCCESSFULLY!")
    except Exception as e:
        print(e)
        print("ERROR, ABORTED.")
        sys.exit(1)
