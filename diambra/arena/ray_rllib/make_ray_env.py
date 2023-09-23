import os
import diambra.arena
from diambra.arena import EnvironmentSettings, WrappersSettings
import logging
import gymnasium as gym
from ray.rllib.env.env_context import EnvContext
from copy import deepcopy
import pickle

class DiambraArena(gym.Env):
    def __init__(self, config: EnvContext):
        self.logger = logging.getLogger(__name__)

        # If to load environment spaces from a file
        self.env_spaces_file_name = "./diambra_ray_env_spaces"
        self.load_spaces_from_file = False

        if "load_spaces_from_file" in config.keys() and config["load_spaces_from_file"] is True:
            if "env_spaces_file_name" not in config.keys():
                raise Exception("Loading environment spaces from file selected, but no file specified.")
            else:
                self.env_spaces_file_name = config["env_spaces_file_name"]

                if not os.path.isfile(self.env_spaces_file_name):
                    raise FileNotFoundError("Unable to load environment spaces from specified file ({}), no file found.".format(self.env_spaces_file_name))
                else:
                    self.load_spaces_from_file = config["load_spaces_from_file"]
        else:
            if "env_spaces_file_name" in config.keys():
                self.env_spaces_file_name = config["env_spaces_file_name"]

        if self.load_spaces_from_file is False:
            if "is_rollout" not in config.keys():
                message = "Environment initialized without a preprocessed config file."
                message += " Make sure to call \"preprocess_ray_config\" before initializing Ray RL Algorithms."
                raise Exception(message)

            self.game_id = config["game_id"]
            self.settings = config["settings"] if "settings" in config.keys() else EnvironmentSettings()
            self.wrappers_settings = config["wrappers_settings"] if "wrappers_settings" in config.keys() else WrappersSettings()
            self.render_mode = config["render_mode"] if "render_mode" in config.keys() else None

            num_rollout_workers = config["num_workers"]
            num_eval_workers = config["evaluation_num_workers"]
            num_envs_per_worker = config["num_envs_per_worker"]
            worker_index = config.worker_index
            vector_index = config.vector_index
            create_env_on_driver = config["create_env_on_driver"]
            is_rollout = config["is_rollout"]

            self.logger.debug("num_rollout_workers: {}".format(num_rollout_workers))
            self.logger.debug("num_eval_workers: {}".format(num_eval_workers))
            self.logger.debug("num_envs_per_worker: {}".format(num_envs_per_worker))
            self.logger.debug("worker_index: {}".format(worker_index))
            self.logger.debug("vector_index: {}".format(vector_index))
            self.logger.debug("create_env_on_driver: {}".format(create_env_on_driver))
            self.logger.debug("is_rollout: {}".format(is_rollout))

            if is_rollout is True:
                self.rank = vector_index + (worker_index - 1) * num_envs_per_worker
            else:
                self.rank = vector_index + (worker_index - 1) * num_envs_per_worker + num_rollout_workers * num_envs_per_worker

            if create_env_on_driver is True:
                self.rank += num_envs_per_worker

            self.logger.debug("Rank: {}".format(self.rank))

            self.env = diambra.arena.make(self.game_id, self.settings, self.wrappers_settings, render_mode=self.render_mode, rank=self.rank)

            env_spaces_dict = {}
            env_spaces_dict["action_space"] = self.env.action_space
            env_spaces_dict["observation_space"] = self.env.observation_space

            # Saving environment spaces
            self.logger.info("Saving environment spaces in: {}".format(self.env_spaces_file_name))
            os.makedirs(os.path.dirname(self.env_spaces_file_name), exist_ok=True)
            env_spaces_file = open(self.env_spaces_file_name, "wb")
            pickle.dump(env_spaces_dict, env_spaces_file)
            env_spaces_file.close()
        else:
            print("Loading environment spaces from: {}".format(self.env_spaces_file_name))
            self.logger.info("Loading environment spaces from: {}".format(self.env_spaces_file_name))
            env_spaces_file = open(self.env_spaces_file_name, "rb")
            # Load Pickle Dict
            env_spaces_dict = pickle.load(env_spaces_file)
            env_spaces_file.close()

        self.action_space = env_spaces_dict["action_space"]
        self.observation_space = env_spaces_dict["observation_space"]

    def reset(self, seed=None, options=None):
        if self.load_spaces_from_file is True:
            return self.observation_space.sample(), {}
        else:
            return self.env.reset(seed=seed, options=options)

    def step(self, action):
        return self.env.step(action)

    def render(self):
        return self.env.render()

def preprocess_ray_config(config):
    logger = logging.getLogger(__name__)

    num_envs_required = 0
    num_envs_per_worker = config["num_envs_per_worker"] if "num_envs_per_worker" in config.keys() else 1

    if "num_workers" not in config.keys():
        config["num_workers"] = 2
    if "create_env_on_driver" not in config.keys():
        config["create_env_on_driver"] = False

    # Set create_env_on_driver appropriately
    if (config["num_workers"] == 0) or\
       (("evaluation_interval" in config.keys() and config["evaluation_interval"] is not None and config["evaluation_interval"] > 0) and\
        ("evaluation_num_workers" not in config.keys() or ("evaluation_num_workers" in config.keys() and config["evaluation_num_workers"] == 0))) :
        config["create_env_on_driver"] = True

    # Count an additional env if create_env_on_driver is set as True
    if config["create_env_on_driver"] is True:
        num_envs_required += num_envs_per_worker

    # Define rollout workers related variables
    num_workers = config["num_workers"]
    # Add rollout workers
    num_envs_required += num_workers*num_envs_per_worker

    # Define evaluation workers related variables
    evaluation_num_workers = config["evaluation_num_workers"] if "evaluation_num_workers" in config.keys() else 0
    # Add evaluation workers
    num_envs_required += evaluation_num_workers*num_envs_per_worker

    logger.debug("Total number of environments required = {}".format(num_envs_required))

    if num_envs_required > diambra.arena.get_num_envs():
        message = "Config file requires more environments than"
        message += " those instantiated by the CLI: {} VS {}.".format(num_envs_required, diambra.arena.get_num_envs())
        message += " Use the CLI option '-s={}' for this configuration.".format(num_envs_required)
        raise Exception(message)
    elif num_envs_required > diambra.arena.get_num_envs():
        message = "Config file requires less environments than"
        message += " those instantiated by the CLI: {} VS {}.".format(num_envs_required, diambra.arena.get_num_envs())
        message += " To avoid wasting resources, use the CLI option '-s={}' for this configuration.".format(num_envs_required)
        logger.warning(message)

    config["env_config"]["create_env_on_driver"] = config["create_env_on_driver"]

    # Setting flag to let the env class know if it is an evaluation env or not
    config["env_config"]["is_rollout"] = True
    config["env_config"]["num_workers"] = num_workers
    config["env_config"]["evaluation_num_workers"] = evaluation_num_workers
    config["env_config"]["num_envs_per_worker"] = num_envs_per_worker

    if "evaluation_config" not in config.keys():
        config["evaluation_config"] = {}
    if "env_config" not in config["evaluation_config"].keys():
        config["evaluation_config"]["env_config"] = deepcopy(config["env_config"])

    config["evaluation_config"]["env_config"]["is_rollout"] = False

    # Deactivating environment checking for submission that loads env spaces from file
    if "load_spaces_from_file" in config["env_config"].keys() and config["env_config"]["load_spaces_from_file"] is True:
        config["disable_env_checking"] = True

    return config

