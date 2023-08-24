import gymnasium as gym
import os
import pickle
import bz2
import json
from threading import Thread
import hashlib

# Save compressed pickle files in parallel
class ParallelPickleWriter(Thread):  # def class type thread
    def __init__(self, save_path, to_save):
        Thread.__init__(self)   # thread init class (don't forget this)

        self.save_path = save_path
        self.to_save = to_save

    def run(self):      # run is a default Thread function
        outfile = bz2.BZ2File(self.save_path, 'w')
        print("Writing RL Trajectory to {} ...".format(self.save_path))
        pickle.dump(self.to_save, outfile)
        print("... done.")
        outfile.close()

# Recursive nested dict print
def nested_dict_obs_space(space, k_list=[], level=0):
    for k in space.spaces:
        v = space[k]
        if isinstance(v, gym.spaces.dict.Dict):
            k_list = k_list[0:level]
            k_list.append(k)
            nested_dict_obs_space(v, k_list, level=level + 1)
        else:
            k_list = k_list[0:level]
            out_string = "observation_space"
            indentation = "    " * level
            for idk in k_list:
                out_string += "[\"{}\"]".format(idk)
            out_string += "[\"{}\"]".format(k)
            out_string = indentation + out_string + ":"
            print(out_string, v)
            if isinstance(v, gym.spaces.MultiDiscrete):
                print(indentation + "Space size:", v.nvec.shape)
            elif isinstance(v, gym.spaces.Discrete):
                pass
            elif isinstance(v, gym.spaces.Box):
                print("        Space type =", v.dtype)
                print("        Space high bound =", v.high)
                print("        Space low bound =", v.low)
            print("")


# Print out environment spaces summary
def env_spaces_summary(env):

    # Printing out observation space description
    print("Observation space:")
    print("")
    if isinstance(env.observation_space, gym.spaces.dict.Dict):
        nested_dict_obs_space(env.observation_space)
    else:
        print("observation_space:", env.observation_space)
        print("    Space type =", env.observation_space.dtype)
        print("    Space high bound =", env.observation_space.high)
        print("    Space low bound =", env.observation_space.low)

    # Printing action spaces
    print("Action space:")
    print("")
    if isinstance(env.action_space, gym.spaces.dict.Dict):

        for k in env.action_space.spaces:
            print("action_space = ", env.action_space[k])
            print("  Space type = ", env.action_space[k].dtype)
            if type(env.action_space[k]) == gym.spaces.MultiDiscrete:
                print("    Space n = ", env.action_space[k].nvec)
            else:
                print("    Space n = ", env.action_space[k].n)
    else:
        print("action_space = ", env.action_space)
        print("  Space type = ", env.action_space.dtype)
        if type(env.action_space) == gym.spaces.MultiDiscrete:
            print("    Space n = ", env.action_space.nvec)
        else:
            print("    Space n = ", env.action_space.n)

# Utility to convert a Gym compliant Dict Space to a standard Dict
def gym_obs_dict_space_to_standard_dict(observation_space_dict):

    standard_dict = {}

    # Looping among all Dict items
    for k, v in observation_space_dict.spaces.items():
        if isinstance(v, gym.spaces.dict.Dict):
            standard_dict[k] = gym_obs_dict_space_to_standard_dict(v)
        else:
            standard_dict[k] = v

    return standard_dict

# Utility to create a Gym compliant Dict Space from the InternalObsDict
def standard_dict_to_gym_obs_dict(obsstandard_dict):

    for k, v in obsstandard_dict.items():
        if isinstance(v, dict):
            obsstandard_dict[k] = standard_dict_to_gym_obs_dict(v)
        else:
            obsstandard_dict[k] = v

    return spaces.Dict(obsstandard_dict)


# Discrete to multidiscrete action conversion
def discrete_to_multi_discrete_action(action, n_move_actions):

    mov_act = 0
    att_act = 0

    if action <= n_move_actions - 1:
        # Move action or no action
        mov_act = action  # For example, for DOA++ this can be 0 - 8
    else:
        # Attack action
        att_act = action - n_move_actions + 1  # E.g. for DOA++ this can be 1 - 7

    return mov_act, att_act

# List all available games
def available_games(print_out=True, details=False):
    base_path = os.path.dirname(os.path.abspath(__file__))
    games_file_path = os.path.join(base_path, 'integratedGames.json')
    games_file = open(games_file_path)
    games_dict = json.load(games_file)

    if print_out:
        for k, v in games_dict.items():
            print("")
            print(" Title: {} - game_id: {}".format(v["name"], v["id"]))
            print(
                "   Difficulty levels: Min {} - Max {}".format(v["difficulty"][0], v["difficulty"][1]))
            if details:
                print("   SHA256 sum: {}".format(v["sha256"]))
                print("   Original ROM name: {}".format(
                    v["original_rom_name"]))
                print("   Search keywords: {}".format(v["search_keywords"]))
                if v["notes"] != "":
                    print("   " + "\033[91m\033[4m\033[1m" + "Notes: {}".format(v["notes"]) + "\033[0m")
                print("   Characters list: {}".format(v["char_list"]))
    else:
        return games_dict

# List sha256 per game
def game_sha_256(game_id=None):

    base_path = os.path.dirname(os.path.abspath(__file__))
    games_file_path = os.path.join(base_path, 'integratedGames.json')
    games_file = open(games_file_path)
    games_dict = json.load(games_file)

    if game_id is None:
        for k, v in games_dict.items():
            print("")
            print(" Title: {}\n ID: {}\n SHA256: {}".format(
                v["name"], v["id"], v["sha256"]))
    else:
        v = games_dict[game_id]
        print(" Title: {}\n ID: {}\n SHA256: {}".format(
            v["name"], v["id"], v["sha256"]))

# Check rom sha256
def sha256_checksum(filename, block_size=65536):
    sha256 = hashlib.sha256()
    with open(filename, 'rb') as f:
        for block in iter(lambda: f.read(block_size), b''):
            sha256.update(block)
    return sha256.hexdigest()


def check_game_sha_256(path, game_id=None):

    base_path = os.path.dirname(os.path.abspath(__file__))
    games_file_path = os.path.join(base_path, 'integratedGames.json')
    games_file = open(games_file_path)
    games_dict = json.load(games_file)

    file_checksum = sha256_checksum(path)

    if game_id is None:

        found = False
        for k, v in games_dict.items():
            if file_checksum == v["sha256"]:
                found = True
                print("Correct ROM file for {}, sha256 = {}".format(
                    v["name"], v["sha256"]))
                break
        if found is False:
            print("ERROR: ROM file not valid")
    else:
        if file_checksum == games_dict[game_id]["sha256"]:
            print("Correct ROM file for {}, sha256 = {}".format(
                games_dict[game_id]["name"], games_dict[game_id]["sha256"]))
        else:
            print("Expected  SHA256 Checksum: {}".format(
                games_dict[game_id]["sha256"]))
            print("Retrieved SHA256 Checksum: {}".format(file_checksum))

# Return number of active environments
def get_num_envs():
    return len(os.getenv("DIAMBRA_ENVS", "").split())
