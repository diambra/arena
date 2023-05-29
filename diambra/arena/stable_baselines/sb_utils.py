from stable_baselines.common.callbacks import BaseCallback
import cv2
import os
import time
import json
import numpy as np
from pathlib import Path

# Visualize Obs content


def show_obs(observation, key_to_add, key_to_add_count, actions_stack,
             n_actions, wait_key, viz, char_list, hardcore, idx_list):

    if not hardcore:
        shp = observation.shape
        for idx in idx_list:
            add_par = observation[:, :, shp[2] - 1]
            add_par = np.reshape(add_par, (-1))

            counter = 0 + idx * int((shp[0] * shp[1]) / 2)

            print("Additional Par P{} =".format(idx + 1), add_par[counter])

            counter += 1

            for idk in range(len(key_to_add)):

                var = add_par[counter:counter + key_to_add_count[idk][idx]]\
                    if key_to_add_count[idk][idx] > 1 else add_par[counter]
                counter += key_to_add_count[idk][idx]

                if "actions" in key_to_add[idk]:
                    move_actions = var[0:actions_stack * n_actions[idx][0]]
                    attack_actions = var[actions_stack * n_actions[idx][0]:actions_stack * (n_actions[idx][0] + n_actions[idx][1])]
                    move_actions = np.reshape(move_actions, (actions_stack, -1))
                    attack_actions = np.reshape(attack_actions, (actions_stack, -1))
                    print("Move actions P{} =\n".format(idx + 1), move_actions)
                    print("Attack actions P{} =\n ".format(idx + 1), attack_actions)
                elif "ownChar" in key_to_add[idk] or "oppChar" in key_to_add[idk]:
                    print("{}P{} =".format(key_to_add[idk], idx + 1), char_list[list(var).index(1.0)])
                else:
                    print("{}P{} =".format(key_to_add[idk], idx + 1), var)

        if viz:
            obs = np.array(observation[:, :, 0:shp[2] - 1]).astype(np.float32)
    else:
        if viz:
            obs = np.array(observation).astype(np.float32)

    if viz:
        for idx in range(obs.shape[2]):
            cv2.imshow("image" + str(idx), obs[:, :, idx])

        cv2.wait_key(wait_key)

# Util to copy P2 additional OBS into P1 position
# on last (add info dedicated) channel


def p2_to_p1_add_obs_move(observation):
    shp = observation.shape
    start_idx = int((shp[0] * shp[1]) / 2)
    observation = np.reshape(observation, (-1))
    num_add_par_p2 = int(observation[start_idx])
    add_par_p2 = observation[start_idx:start_idx + num_add_par_p2 + 1]
    observation[0:num_add_par_p2 + 1] = add_par_p2
    observation = np.reshape(observation, (shp[0], -1))
    return observation

# Linear scheduler for RL agent parameters
def linear_schedule(initial_value, final_value=0.0):
    """
    Linear learning rate schedule.
    :param initial_value: (float or str)
    :return: (function)
    """
    if isinstance(initial_value, str):
        initial_value = float(initial_value)
        final_value = float(final_value)
        assert (initial_value > 0.0), "linear_schedule work only with positive decreasing values"

    def func(progress):
        """
        Progress will decrease from 1 (beginning) to 0
        :param progress: (float)
        :return: (float)
        """
        return final_value + progress * (initial_value - final_value)

    return func

# AutoSave Callback
class AutoSave(BaseCallback):
    """
    Callback for saving a model, it is saved every ``check_freq`` steps

    :param check_freq: (int)
    :param save_path: (str) Path to the folder where the model will be saved.
    :filename_prefix: (str) Filename prefix
    :param verbose: (int)
    """
    def __init__(self, check_freq: int, num_envs: int, save_path: str, filename_prefix: str="", verbose: int=1):
        super(AutoSave, self).__init__(verbose)
        self.check_freq = int(check_freq / num_envs)
        self.num_envs = num_envs
        self.save_path_base = Path(save_path)
        self.filename = filename_prefix + "autosave_"

    def _on_step(self) -> bool:
        if self.n_calls % self.check_freq == 0:
            if self.verbose > 0:
                print("Saving latest model to {}".format(self.save_path_base))
            # Save the agent
            self.model.save(self.save_path_base / (self.filename + str(self.n_calls * self.num_envs)))

        return True

# Update p2Brain model Callback


class UpdateRLPolicyWeights(BaseCallback):
    def __init__(self, check_freq: int, num_envs: int, save_path: str,
                 prev_agents_sampling={"probability": 0.0, "list": []}, verbose=1):
        super(UpdateRLPolicyWeights, self).__init__(verbose)
        self.check_freq = int(check_freq / num_envs)
        self.num_envs = num_envs
        self.save_path = os.path.join(save_path, 'lastModel')
        self.sampling_probability = prev_agents_sampling["probability"]
        self.prev_agents_list = prev_agents_sampling["list"]
        time_dep_seed = int((time.time() - int(time.time() - 0.5)) * 1000)
        np.random.seed(time_dep_seed)

    def _on_step(self) -> bool:
        if self.n_calls % self.check_freq == 0:
            # Selects if using previous agent or the last saved one
            if np.random.rand() < self.sampling_probability:
                # Sample an old model from the list
                if self.verbose > 0:
                    print("Using an older model")

                # Sample one of the older models
                idx = int(np.random.rand() * len(self.prev_agents_list))
                weights_paths_sampled = self.prev_agents_list[idx]

                # Load new weights
                self.training_env.env_method("update_p2_policy_weights",
                                             weights_path=weights_paths_sampled)
            else:
                # Use the last saved model
                if self.verbose > 0:
                    print("Using last saved model")

                if self.verbose > 0:
                    print("Saving latest model to {}".format(self.save_path))

                # Save the agent
                self.model.save(self.save_path)

                # Load new weights
                self.training_env.env_method("update_p2_policy_weights",
                                             weights_path=self.save_path)

        return True

# Model CFG save


def model_cfg_save(model_path, name, n_actions, char_list,
                   settings, wrappers_settings, key_to_add, params):
    data = {}
    _, model_name = os.path.split(model_path)
    data["agentModel"] = model_name + ".zip"
    data["name"] = name
    data["n_actions"] = n_actions
    data["char_list"] = char_list
    data["settings"] = settings
    data["wrappers_settings"] = wrappers_settings
    data["key_to_add"] = key_to_add
    data["params"] = params

    with open(model_path + ".json", 'w') as outfile:
        json.dump(data, outfile, indent=4)


def key_to_add_count_calc(key_to_add, n_actions, n_actions_stack, char_list):

    key_to_add_count = []

    for key in key_to_add:
        if "actions" in key:
            key_to_add_count.append([n_actions_stack * (n_actions[0] + n_actions[1])])
        elif "Char" in key:
            key_to_add_count.append([len(char_list)])
        else:
            key_to_add_count.append([1])

    return key_to_add_count

# Abort training when run out of recorded trajectories for imitation learning


class ImitationLearningExhaustedExamples(BaseCallback):
    """
    Callback for aborting training when run out of Imitation Learning examples
    """
    def __init__(self):
        super(ImitationLearningExhaustedExamples, self).__init__()

    def _on_step(self) -> bool:

        return np.any(self.env.get_attr("exhausted"))
