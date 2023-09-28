import diambra.arena
from diambra.arena import SpaceTypes, EnvironmentSettings, WrappersSettings

def main():
    # Environment settings
    settings = EnvironmentSettings()
    settings.action_space = SpaceTypes.MULTI_DISCRETE

    # Gym wrappers settings
    wrappers_settings = WrappersSettings()

    ### Generic wrappers

    # Number of no-Op actions to be executed
    # at the beginning of the episode (0 by default)
    wrappers_settings.no_op_max = 0

    # Number of steps for which the same action should be sent (1 by default)
    wrappers_settings.repeat_action = 1

    ### Reward wrappers

    # Wrapper option for reward normalization
    # When activated, the reward normalization factor can be set (default = 0.5)
    # The normalization is performed by dividing the reward value
    # by the product of the factor times the value of the full health bar
    # reward = reward / (C * fullHealthBarValue)
    wrappers_settings.normalize_reward = True
    wrappers_settings.normalization_factor = 0.5

    # If to clip rewards (False by default)
    wrappers_settings.clip_reward = False

    ### Action space wrapper(s)

    # Limit the action space to single attack buttons, removing attack buttons combinations (False by default)
    wrappers_settings.no_attack_buttons_combinations = False

    ### Observation space wrapper(s)

    # Frame resize operation spec (deactivated by default)
    # WARNING: for speedup, avoid frame warping wrappers,
    #          use environment's native frame wrapping through
    #          "frame_shape" setting (see documentation for details).
    wrappers_settings.frame_shape = (128, 128, 1)

    # Number of frames to be stacked together (1 by default)
    wrappers_settings.stack_frames = 4

    # Frames interval when stacking (1 by default)
    wrappers_settings.dilation = 1

    # Add last action to observation (False by default)
    wrappers_settings.add_last_action = True

    # How many past actions to stack together (1 by default)
    # NOTE: needs "add_last_action_to_observation" wrapper to be active
    wrappers_settings.stack_actions = 6

    # If to scale observation numerical values (False by default)
    # optionally exclude images from normalization (False by default)
    # and optionally perform one-hot encoding also on discrete binary variables (False by default)
    wrappers_settings.scale = True
    wrappers_settings.exclude_image_scaling = True
    wrappers_settings.process_discrete_binary = False

    # If to make the observation relative to the agent as a function to its role (P1 or P2) (deactivate by default)
    # i.e.:
    #  - In 1P environments, if the agent is P1 then the observation "P1" nesting level becomes "own" and "P2" becomes "opp"
    #  - In 2P environments, if "agent_0" role is P1 and "agent_1" role is P2, then the player specific nesting levels observation (P1 - P2)
    #    are grouped under "agent_0" and "agent_1", and:
    #    - Under "agent_0", "P1" nesting level becomes "own" and "P2" becomes "opp"
    #    - Under "agent_1", "P1" nesting level becomes "opp" and "P2" becomes "own"
    wrappers_settings.role_relative = True

    # Flattening observation dictionary and filtering
    # a sub-set of the RAM states
    wrappers_settings.flatten = True
    wrappers_settings.filter_keys = ["stage", "timer", "action", "own_side", "opp_side",
                                     "own_health", "opp_health", "opp_character"]

    env = diambra.arena.make("doapp", settings, wrappers_settings, render_mode="human")

    observation, info = env.reset(seed=42)
    env.unwrapped.show_obs(observation)

    while True:
        actions = env.action_space.sample()
        print("Actions: {}".format(actions))

        observation, reward, terminated, truncated, info = env.step(actions)
        done = terminated or truncated
        env.unwrapped.show_obs(observation)
        print("Reward: {}".format(reward))
        print("Done: {}".format(done))
        print("Info: {}".format(info))

        if done:
            observation, info = env.reset()
            env.unwrapped.show_obs(observation)
            break

    env.close()

    # Return success
    return 0

if __name__ == '__main__':
    main()