from stable_baselines3.common.callbacks import BaseCallback
from pathlib import Path

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
