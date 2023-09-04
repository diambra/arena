from stable_baselines.common.callbacks import BaseCallback
import cv2
import numpy as np
from pathlib import Path

# Visualize Obs content
def show_obs(observation, ram_states_list, n_actions, n_actions_stack, char_list, viz=False, wait_key=1):

    shp = observation.shape
    ram_states = observation[:, :, shp[2] - 1]
    ram_states = np.reshape(ram_states, (-1))

    counter = 0

    print("RAM states =", ram_states[counter])

    counter += 1
    if "action_move" in ram_states_list and "action_attack" in ram_states_list:
        n_values = n_actions_stack * (n_actions[0] + n_actions[1])
        var = ram_states[counter:counter + n_values]
        counter += n_values
        move_actions = var[0:n_actions_stack * n_actions[0]]
        attack_actions = var[n_actions_stack * n_actions[0]:n_values]
        move_actions = np.reshape(move_actions, (n_actions_stack, -1))
        attack_actions = np.reshape(attack_actions, (n_actions_stack, -1))
        print("Move actions =\n", move_actions)
        print("Attack actions =\n ", attack_actions)
        ram_states_list = [element for element in ram_states_list if element != "action_move" and element != "action_attack"]

    for ram_state_key in ram_states_list:
        if "own_char" in ram_state_key or "opp_char" in ram_state_key:
            var = ram_states[counter:counter + len(char_list)]
            counter += len(char_list)
            print("{} = {}".format(ram_state_key, char_list[list(var).index(1.0)]))
        else:
            var = ram_states[counter:counter + 1]
            counter += 1
            print("{} = {}".format(ram_state_key, var))

    if viz:
        obs = np.array(observation[:, :, 0:shp[2] - 1]).astype(np.float32)
        for idx in range(obs.shape[2]):
            cv2.imshow("image" + str(idx), obs[:, :, idx])

        cv2.waitKey(wait_key)

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
