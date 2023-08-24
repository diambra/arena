import diambra.arena

def main():
    # Environment settings
    settings = {"n_players": 2} # Nested dictionaries are only present in 2P envs

    # Gym wrappers settings
    wrappers_settings = {}

    # Number of no-Op actions to be executed
    # at the beginning of the episode (0 by default)
    wrappers_settings["no_op_max"] = 0

    # Number of steps for which the same action should be sent (1 by default)
    wrappers_settings["sticky_actions"] = 1

    # Frame resize operation spec (deactivated by default)
    # WARNING: for speedup, avoid frame warping wrappers,
    #          use environment's native frame wrapping through
    #          "frame_shape" setting (see documentation for details).
    wrappers_settings["frame_shape"] = (128, 128, 1)

    # Wrapper option for reward normalization
    # When activated, the reward normalization factor can be set (default = 0.5)
    # The normalization is performed by dividing the reward value
    # by the product of the factor times the value of the full health bar
    # reward = reward / (C * fullHealthBarValue)
    wrappers_settings["reward_normalization"] = True
    wrappers_settings["reward_normalization_factor"] = 0.5

    # If to clip rewards (False by default)
    wrappers_settings["clip_rewards"] = False

    # Number of frames to be stacked together (1 by default)
    wrappers_settings["frame_stack"] = 4

    # Frames interval when stacking (1 by default)
    wrappers_settings["dilation"] = 1

    # How many past actions to stack together (1 by default)
    wrappers_settings["actions_stack"] = 12

    # If to scale observation numerical values (deactivated by default)
    # optionally exclude images from normalization (deactivated by default)
    # and optionally perform one-hot encoding also on discrete binary variables (deactivated by default)
    wrappers_settings["scale"] = True
    wrappers_settings["exclude_image_scaling"] = True
    wrappers_settings["process_discrete_binary"] = True

    # Scaling interval (0 = [0.0, 1.0], 1 = [-1.0, 1.0])
    wrappers_settings["scale_mod"] = 0

    # Flattening observation dictionary and filtering
    # a sub-set of the RAM states
    wrappers_settings["flatten"] = True
    wrappers_settings["filter_keys"] = ["stage", "timer", "agent_0_own_side", "agent_0_opp_side",
                                        "agent_0_own_health", "agent_0_opp_char",
                                        "agent_0_action_move", "agent_0_action_attack"]

    env = diambra.arena.make("doapp", settings, wrappers_settings, render_mode="human")

    observation, info = env.reset(seed=42)
    env.show_obs(observation)

    while True:
        actions = env.action_space.sample()
        print("Actions: {}".format(actions))

        observation, reward, terminated, truncated, info = env.step(actions)
        done = terminated or truncated
        env.show_obs(observation)
        print("Reward: {}".format(reward))
        print("Done: {}".format(done))
        print("Info: {}".format(info))

        if done:
            observation, info = env.reset()
            env.show_obs(observation)
            break

    env.close()

    # Return success
    return 0

if __name__ == '__main__':
    main()