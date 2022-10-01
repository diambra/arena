import sys
import os
import time
base_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(base_path, '../'))
from make_sb_env import make_sb_env
from sb_utils import linear_schedule
from custom_policies.custom_cnn_policy import CustCnnPolicy, local_nature_cnn_small
from stable_baselines import PPO2

if __name__ == '__main__':
    time_dep_seed = int((time.time()-int(time.time()-0.5))*1000)

    # Settings settings
    settings = {}
    settings["game_id"] = "doapp"
    settings["step_satio"] = 6
    settings["frame_shape"] = [128, 128, 1]
    settings["player"] = "Random"  # P1 / P2

    settings["characters"] = [["Random", "Random", "Random"], ["Random", "Random", "Random"]]

    settings["difficulty"] = 3
    settings["char_outfits"] = [2, 2]

    settings["action_space"] = "discrete"
    settings["attack_but_combination"] = False

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

    # Additional obs key list
    key_to_add = []
    key_to_add.append("actions")
    key_to_add.append("ownHealth")
    key_to_add.append("oppHealth")
    key_to_add.append("ownSide")
    key_to_add.append("oppSide")
    key_to_add.append("stage")

    key_to_add.append("ownChar")
    key_to_add.append("oppChar")

    env, num_env = make_sb_env(time_dep_seed, settings, wrappers_settings,
                               key_to_add=key_to_add, use_subprocess=True)

    # Policy param
    n_actions = env.get_attr("n_actions")[0][0]
    n_actions_stack = env.get_attr("n_actions_stack")[0]
    n_char = env.get_attr("number_of_characters")[0]
    char_names = env.get_attr("char_names")[0]

    policy_kwargs = {}
    policy_kwargs["n_add_info"] = n_actions_stack*(n_actions[0]+n_actions[1]) + \
        len(key_to_add)-3 + 2*n_char
    policy_kwargs["layers"] = [64, 64]

    policy_kwargs["cnn_extractor"] = local_nature_cnn_small

    print("n_actions =", n_actions)
    print("n_char =", n_char)
    print("n_add_info =", policy_kwargs["n_add_info"])

    # PPO param
    gamma = 0.94
    learning_rate = linear_schedule(2.5e-4, 2.5e-6)
    cliprange = linear_schedule(0.15, 0.025)
    cliprange_vf = cliprange
    n_steps = 128

    # Initialize the agent
    agent = PPO2(CustCnnPolicy, env, verbose=1,
                 gamma=gamma, nminibatches=4, noptepochs=4, n_steps=n_steps,
                 learning_rate=learning_rate, cliprange=cliprange,
                 cliprange_vf=cliprange_vf, policy_kwargs=policy_kwargs)

    print("Model discount factor = ", agent.gamma)

    # Train the agent
    time_steps = n_steps*2*num_env
    tic = time.time()
    agent.learn(total_timesteps=time_steps)
    toc = time.time()

    print("Time elapsed = ", toc-tic)

    # Close the environment
    env.close()
