#!/usr/bin/env python3
import diambra.arena
from diambra.arena import SpaceTypes, Roles
from diambra.arena.utils.gym_utils import env_spaces_summary, discrete_to_multi_discrete_action
import random
import numpy as np
import warnings

default_args = {
    "interactive": False,
    "n_episodes": 1,
    "no_action_probability": 0.0,
    "render": False,
    "log_output": False,
}

def env_exec(settings, options_list, wrappers_settings, episode_recording_settings, args=default_args):
    try:
        wait_key = 1
        if args["interactive"] is True:
            wait_key = 0

        n_rounds = 2
        if settings["game_id"] == "kof98umh":
            n_rounds = 3

        env = diambra.arena.make(settings["game_id"], settings, wrappers_settings, episode_recording_settings)

        # Print environment obs and action spaces summary
        if args["log_output"] is True:
            env_spaces_summary(env)

        for options in options_list:
            observation, info = env.reset(options=options)
            if args["log_output"] is True:
                env.show_obs(observation, wait_key, args["render"])

            cumulative_ep_rew = 0.0
            cumulative_ep_rew_all = []

            max_num_ep = args["n_episodes"]
            curr_num_ep = 0

            no_action = random.choices([True, False], [args["no_action_probability"], 1.0 - args["no_action_probability"]])[0]

            while curr_num_ep < max_num_ep:
                actions = env.action_space.sample()

                if env.env_settings.n_players == 1:
                    if no_action is True:
                        actions = env.get_no_op_action()

                    if env.env_settings.action_space == SpaceTypes.DISCRETE:
                        move_action, att_action = discrete_to_multi_discrete_action(actions, env.n_actions[0])
                    else:
                        move_action, att_action = actions[0], actions[1]

                    if args["log_output"] is True:
                        print("(agent_0) {} {}".format(env.print_actions_dict[0][move_action], env.print_actions_dict[1][att_action]))

                else:
                    if no_action is True:
                        actions["agent_0"] = env.get_no_op_action()["agent_0"]

                    for idx in range(env.env_settings.n_players):
                        if env.env_settings.action_space[idx] == SpaceTypes.DISCRETE:
                            move_action, att_action = discrete_to_multi_discrete_action(actions["agent_{}".format(idx)], env.n_actions[0])
                        else:
                            move_action, att_action = actions["agent_{}".format(idx)][0], actions["agent_{}".format(idx)][1]

                        if args["log_output"] is True:
                            print("(agent_{}) {} {}".format(idx, env.print_actions_dict[0][move_action], env.print_actions_dict[1][att_action]))

                observation, reward, terminated, truncated, info = env.step(actions)

                cumulative_ep_rew += reward
                if args["log_output"] is True:
                    print("action =", actions)
                    print("reward =", reward)
                    print("done =", terminated or truncated)
                    for k, v in info.items():
                        print("info[\"{}\"] = {}".format(k, v))
                    env.show_obs(observation, wait_key, args["render"])
                    print("--")
                    print("Current Cumulative Reward =", cumulative_ep_rew)

                    print("----------")

                if terminated or truncated:
                    observation, info = env.reset()
                    if args["log_output"] is True:
                        env.show_obs(observation, wait_key, args["render"])
                        print("Ep. # = ", curr_num_ep)
                        print("Ep. Cumulative Rew # = ", cumulative_ep_rew)
                    curr_num_ep += 1
                    no_action = random.choices([True, False], [args["no_action_probability"], 1.0 - args["no_action_probability"]])[0]
                    cumulative_ep_rew_all.append(cumulative_ep_rew)
                    cumulative_ep_rew = 0.0

                if info["round_done"]:
                    # Side check when no wrappers active:
                    if len(wrappers_settings) == 0:
                        if (observation["P1"]["side"] != 0.0 or observation["P2"]["side"] != 1.0):
                            raise RuntimeError("Wrong starting sides:", observation["P1"]["side"], observation["P2"]["side"])

                    elif ("frame_shape" in wrappers_settings.keys() and wrappers_settings["frame_shape"][2] == 1):
                        # Frames equality check
                        frame = observation["frame"]

                        for frame_idx in range(frame.shape[2] - 1):
                            if np.any(frame[:, :, frame_idx] != frame[:, :, frame_idx + 1]):
                                raise RuntimeError("Frames inside observation after round/stage/game/episode done are "
                                                "not equal. Dones =", info["round_done"], info["stage_done"],
                                                info["game_done"], info["episode_done"])

            if args["log_output"] is True:
                print("Cumulative reward = ", cumulative_ep_rew_all)
                print("Mean cumulative reward = ", np.mean(cumulative_ep_rew_all))
                print("Std cumulative reward = ", np.std(cumulative_ep_rew_all))

            if len(cumulative_ep_rew_all) != max_num_ep:
                raise RuntimeError("Not run all episodes")

            if env.env_settings.continue_game <= 0.0 and env.env_settings.n_players == 1:
                max_continue = int(-env.env_settings.continue_game)
            else:
                max_continue = 0

            if env.env_settings.game_id == "tektagt":
                max_continue = (max_continue + 1) * 0.7 - 1

            round_max_reward = env.max_delta_health / env.reward_normalization_value
            if (no_action is True and (np.mean(cumulative_ep_rew_all) > -(max_continue + 1) * round_max_reward * n_rounds + 0.001)):
                message = "NoAction policy and average reward different than {} ({})".format(
                    -(max_continue + 1) * round_max_reward * n_rounds, np.mean(cumulative_ep_rew_all))
                warnings.warn(UserWarning(message))

        env.close()

        print("COMPLETED SUCCESSFULLY!")
        return 0
    except Exception as e:
        print(e)
        print("ERROR, ABORTED.")
        return 1
