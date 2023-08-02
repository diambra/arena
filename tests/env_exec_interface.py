#!/usr/bin/env python3
import diambra.arena
from diambra.arena.utils.gym_utils import env_spaces_summary, discrete_to_multi_discrete_action
import time
import numpy as np
import warnings

default_args = {
    "interactive": False,
    "n_episodes": 1,
    "no_action": False,
    "render": False
}

def env_exec(settings, wrappers_settings, episode_recording_settings, args=default_args):

    try:
        wait_key = 1
        if args["interactive"] is True:
            wait_key = 0

        no_action = args["no_action"]

        n_rounds = 2
        if settings["game_id"] == "kof98umh":
            n_rounds = 3

        env = diambra.arena.make(settings["game_id"], settings, wrappers_settings, episode_recording_settings)

        # Print environment obs and action spaces summary
        env_spaces_summary(env)

        observation = env.reset()
        env.show_obs(observation, wait_key, args["render"])

        cumulative_ep_rew = 0.0
        cumulative_ep_rew_all = []

        max_num_ep = args["n_episodes"]
        curr_num_ep = 0

        while curr_num_ep < max_num_ep:

            actions = env.action_space.sample()

            if env.env_settings.n_players == 1:
                if no_action is True:
                    if env.env_settings.action_space == "multi_discrete":
                        for iel, _ in enumerate(actions):
                            actions[iel] = 0
                    else:
                        actions = 0

                if env.env_settings.action_space == "discrete":
                    move_action, att_action = discrete_to_multi_discrete_action(actions, env.n_actions[0])
                else:
                    move_action, att_action = actions[0], actions[1]

                print("(agent_0) {} {}".format(env.print_actions_dict[0][move_action], env.print_actions_dict[1][att_action]))

            else:
                if no_action is True:
                    if env.env_settings.action_space[0] == "multi_discrete":
                        actions["agent_0"] = np.array([0, 0])
                    else:
                        actions["agent_0"] = 0

                for idx in range(env.env_settings.n_players):
                    if env.env_settings.action_space[idx] == "discrete":
                        move_action, att_action = discrete_to_multi_discrete_action(actions["agent_{}".format(idx)], env.n_actions[0])
                    else:
                        move_action, att_action = actions["agent_{}".format(idx)][0], actions["agent_{}".format(idx)][1]

                    print("(agent_{}) {} {}".format(idx, env.print_actions_dict[0][move_action], env.print_actions_dict[1][att_action]))

            observation, reward, done, info = env.step(actions)

            cumulative_ep_rew += reward
            print("action =", actions)
            print("reward =", reward)
            print("done =", done)
            for k, v in info.items():
                print("info[\"{}\"] = {}".format(k, v))
            env.show_obs(observation, wait_key, args["render"])
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
                env.show_obs(observation, wait_key, args["render"])

            if np.any([info["round_done"], info["stage_done"], info["game_done"], info["episode_done"]]):
                # Side check
                if env.env_settings.n_players == 1:
                    ram_state_values = [observation["own_side"], observation["opp_side"]]
                else:
                    if "agent_0_own_side" in observation.keys():
                        ram_state_values = [observation["agent_0_own_side"], observation["agent_0_opp_side"]]
                    else:
                        ram_state_values = [observation["agent_0"]["own_side"], observation["agent_0"]["opp_side"]]

                if env.env_settings.pb_model.variable_env_settings.player_env_settings[0].role == "P2":
                    if (ram_state_values[0] != 1.0 or ram_state_values[1] != 0.0):
                        raise RuntimeError("Wrong starting sides:", ram_state_values[0], ram_state_values[1])
                else:
                    if (ram_state_values[0] != 0.0 or ram_state_values[1] != 1.0):
                        raise RuntimeError("Wrong starting sides:", ram_state_values[0], ram_state_values[1])

                frame = observation["frame"]

                # Frames equality check
                if ("hwc_obs_resize" in wrappers_settings.keys() and wrappers_settings["hwc_obs_resize"][2] == 1):
                    for frame_idx in range(frame.shape[2] - 1):
                        if np.any(frame[:, :, frame_idx] != frame[:, :, frame_idx + 1]):
                            raise RuntimeError("Frames inside observation after round/stage/game/episode done are "
                                               "not equal. Dones =", info["round_done"], info["stage_done"],
                                               info["game_done"], info["episode_done"])

        print("Cumulative reward = ", cumulative_ep_rew_all)
        print("Mean cumulative reward = ", np.mean(cumulative_ep_rew_all))
        print("Std cumulative reward = ", np.std(cumulative_ep_rew_all))

        env.close()

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

        print("COMPLETED SUCCESSFULLY!")
        return 0
    except Exception as e:
        print(e)
        print("ERROR, ABORTED.")
        return 1
