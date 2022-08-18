#!/usr/bin/env python3
import diambra.arena
from diambra.arena.utils.gym_utils import env_spaces_summary,\
    discrete_to_multi_discrete_action, show_gym_obs
import argparse
import time
import numpy as np

if __name__ == '__main__':
    time_dep_seed = int((time.time() - int(time.time() - 0.5)) * 1000)

    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--gameId', type=str, default="doapp", help='Game ID [(doapp), sfiii3n, tektagt, umk3]')
        parser.add_argument('--player', type=str, default="Random", help='Player (Random)')
        parser.add_argument('--character1', type=str, default="Random", help='Character P1 (Random)')
        parser.add_argument('--character2', type=str, default="Random", help='Character P2 (Random)')
        parser.add_argument('--character1_2', type=str, default="Random", help='Character P1_2 (Random)')
        parser.add_argument('--character2_2', type=str, default="Random", help='Character P2_2 (Random)')
        parser.add_argument('--character1_3', type=str, default="Random", help='Character P1_3 (Random)')
        parser.add_argument('--character2_3', type=str, default="Random", help='Character P2_3 (Random)')
        parser.add_argument('--stepRatio', type=int, default=3, help='Frame ratio')
        parser.add_argument('--nEpisodes', type=int, default=1, help='Number of episodes')
        parser.add_argument('--continueGame', type=float, default=-1.0, help='ContinueGame flag (-inf,+1.0]')
        parser.add_argument('--actionSpace', type=str, default="discrete", help='discrete/multi_discrete')
        parser.add_argument('--attButComb', type=int, default=0, help='Use attack button combinations (0=F)/1=T')
        parser.add_argument('--noAction', type=int, default=0, help='If to use no action policy (0=False)')
        parser.add_argument('--hardcore', type=int, default=0, help='Hard core mode (0=False)')
        parser.add_argument('--interactiveViz', type=int, default=0, help='Interactive Visualization (0=False)')
        parser.add_argument('--envAddress', type=str, default="", help='diambraEngine Address')
        opt = parser.parse_args()
        print(opt)

        viz_flag = bool(opt.interactiveViz)
        wait_key = 1
        if viz_flag:
            wait_key = 0

        # Settings
        settings = {}
        if opt.envAddress != "":
            settings["env_address"] = opt.envAddress
        settings["player"] = opt.player
        settings["characters"] = [[opt.character1,
                                   opt.character1_2,
                                   opt.character1_3],
                                  [opt.character2,
                                   opt.character2_2,
                                   opt.character2_3]]

        settings["step_ratio"] = opt.stepRatio
        settings["continue_game"] = opt.continueGame
        settings["show_final"] = False

        settings["char_outfits"] = [2, 2]

        settings["action_space"] = [opt.actionSpace, opt.actionSpace]
        settings["attack_but_combination"] = [opt.attButComb, opt.attButComb]
        if settings["player"] != "P1P2":
            settings["action_space"] = settings["action_space"][0]
            settings["attack_but_combination"] = settings["attack_but_combination"][0]

        n_rounds = 2
        if opt.gameId == "kof98umh":
            n_rounds = 3

        hardcore = False if opt.hardcore == 0 else True
        settings["hardcore"] = hardcore

        env = diambra.arena.make(opt.gameId, settings, seed=time_dep_seed)

        # Print environment obs and action spaces summary
        env_spaces_summary(env)

        observation = env.reset()

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
                        for iel, _ in enumerate(actions):
                            actions[iel] = 0
                    else:
                        actions = 0

                if settings["action_space"] == "discrete":
                    move_action, att_action = discrete_to_multi_discrete_action(
                        actions, env.n_actions[0][0])
                else:
                    move_action, att_action = actions[0], actions[1]

                print("(P1) {} {}".format(env.print_actions_dict[0][move_action],
                                          env.print_actions_dict[1][att_action]))

            else:
                for idx in range(2):
                    actions[idx] = env.action_space["P{}".format(idx + 1)].sample()

                    if opt.noAction == 1 and idx == 0:
                        if settings["action_space"][idx] == "multi_discrete":
                            for iel, _ in enumerate(actions[idx]):
                                actions[idx][iel] = 0
                        else:
                            actions[idx] = 0

                    if settings["action_space"][idx] == "discrete":
                        move_action, att_action = discrete_to_multi_discrete_action(
                            actions[idx], env.n_actions[idx][0])
                    else:
                        move_action, att_action = actions[idx][0], actions[idx][1]

                    print("(P{}) {} {}".format(idx + 1, env.print_actions_dict[0][move_action],
                                               env.print_actions_dict[1][att_action]))

            if (settings["player"] == "P1P2" or settings["action_space"] != "discrete"):
                actions = np.append(actions[0], actions[1])

            observation, reward, done, info = env.step(actions)

            cumulative_ep_rew += reward
            print("action =", actions)
            print("reward =", reward)
            print("done =", done)
            for k, v in info.items():
                print("info[\"{}\"] = {}".format(k, v))
            show_gym_obs(observation, env.char_names, wait_key, viz_flag)
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
                show_gym_obs(observation, env.char_names, wait_key, viz_flag)

            if np.any([info["round_done"], info["stage_done"],
                       info["game_done"], info["ep_done"]]):

                if hardcore is False:
                    # Side check
                    if env.player_side == "P2":
                        if observation["P1"]["ownSide"] != 1.0 or observation["P1"]["oppSide"] != 0.0:
                            raise RuntimeError("Wrong starting side:", observation["P1"]["ownSide"],
                                               observation["P1"]["oppSide"])
                    else:
                        if observation["P1"]["ownSide"] != 0.0 or observation["P1"]["oppSide"] != 1.0:
                            raise RuntimeError("Wrong starting side:", observation["P1"]["ownSide"],
                                               observation["P1"]["oppSide"])

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

        if (opt.noAction == 1
                and (np.mean(cumulative_ep_rew_all) > - n_rounds * (max_continue + 1) *
                     env.max_delta_health + 0.001)):
            raise RuntimeError("NoAction policy and average "
                               "reward different than {} ({})".format(
                                   - n_rounds * (max_continue + 1) * env.max_delta_health,
                                   np.mean(cumulative_ep_rew_all)))

        print("ALL GOOD!")
    except Exception as e:
        print(e)
        print("ALL BAD")
