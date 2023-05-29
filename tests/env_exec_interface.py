#!/usr/bin/env python3
import diambra.arena
from diambra.arena.utils.gym_utils import env_spaces_summary, discrete_to_multi_discrete_action
import time
import numpy as np
import warnings

default_args = {
    "interactive_viz": False,
    "n_episodes": 1,
    "no_action": False
}

def env_exec(settings, wrappers_settings, traj_rec_settings, args=default_args):

    try:
        time_dep_seed = int((time.time() - int(time.time() - 0.5)) * 1000)

        wait_key = 1
        if args["interactive_viz"] is True:
            wait_key = 0

        no_action = args["no_action"]

        n_rounds = 2
        if settings["game_id"] == "kof98umh":
            n_rounds = 3

        env = diambra.arena.make(settings["game_id"], settings, wrappers_settings, traj_rec_settings, seed=time_dep_seed)

        # Print environment obs and action spaces summary
        env_spaces_summary(env)

        observation = env.reset()

        cumulative_ep_rew = 0.0
        cumulative_ep_rew_all = []

        max_num_ep = args["n_episodes"]
        curr_num_ep = 0

        while curr_num_ep < max_num_ep:

            actions = [None, None]
            if settings["player"] != "P1P2":
                actions = env.action_space.sample()

                if no_action is True:
                    if settings["action_space"] == "multi_discrete":
                        for iel, _ in enumerate(actions):
                            actions[iel] = 0
                    else:
                        actions = 0

                if settings["action_space"] == "discrete":
                    move_action, att_action = discrete_to_multi_discrete_action(
                        actions, env.n_actions[0])
                else:
                    move_action, att_action = actions[0], actions[1]

                print("(P1) {} {}".format(env.print_actions_dict[0][move_action],
                                          env.print_actions_dict[1][att_action]))

            else:
                for idx in range(2):
                    actions[idx] = env.action_space["P{}".format(idx + 1)].sample()

                    if no_action is True and idx == 0:
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
            env.show_obs(observation, wait_key)
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
                env.show_obs(observation, wait_key)

            if np.any([info["round_done"], info["stage_done"], info["game_done"], info["ep_done"]]):

                if settings["hardcore"] is False:
                    # Side check
                    if "P1_ownSide" in observation.keys():
                        ram_state_values = [observation["P1_ownSide"], observation["P1_oppSide"]]
                    else:
                        ram_state_values = [observation["P1"]["ownSide"], observation["P1"]["oppSide"]]

                    if env.player_side == "P2":
                        if (ram_state_values[0] != 1.0 or ram_state_values[1] != 0.0):
                            raise RuntimeError("Wrong starting sides:", ram_state_values[0], ram_state_values[1])
                    else:
                        if (ram_state_values[0] != 0.0 or ram_state_values[1] != 1.0):
                            raise RuntimeError("Wrong starting sides:", ram_state_values[0], ram_state_values[1])

                    frame = observation["frame"]
                else:
                    frame = observation

                # Frames equality check
                if ("hwc_obs_resize" in wrappers_settings.keys() and wrappers_settings["hwc_obs_resize"][2] == 1):
                    for frame_idx in range(frame.shape[2] - 1):
                        if np.any(frame[:, :, frame_idx] != frame[:, :, frame_idx + 1]):
                            raise RuntimeError("Frames inside observation after "
                                               "round/stage/game/episode done are "
                                               "not equal. Dones =", info["round_done"], info["stage_done"],
                                               info["game_done"], info["ep_done"])

        print("Cumulative reward = ", cumulative_ep_rew_all)
        print("Mean cumulative reward = ", np.mean(cumulative_ep_rew_all))
        print("Std cumulative reward = ", np.std(cumulative_ep_rew_all))

        env.close()

        if len(cumulative_ep_rew_all) != max_num_ep:
            raise RuntimeError("Not run all episodes")

        if settings["continue_game"] <= 0.0 and settings["player"] != "P1P2":
            max_continue = int(-settings["continue_game"])
        else:
            max_continue = 0

        if settings["game_id"] == "tektagt":
            max_continue = (max_continue + 1) * 0.7 - 1

        round_max_reward = env.max_delta_health / env.reward_normalization_value
        if (no_action is True and (np.mean(cumulative_ep_rew_all) > -(max_continue + 1) * round_max_reward * n_rounds + 0.001)):

            message = "NoAction policy and average reward different than {} ({})".format(
                -(max_continue + 1) * round_max_reward * n_rounds, np.mean(cumulative_ep_rew_all))
            warnings.warn(UserWarning(message))

        print("COMPLETED SUCCESSFULLY!")
        return 0
    except Exception as e:
        print(e)
        print("ERROR, ABORTED.")
        return 1
