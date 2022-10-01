import gym
from gym import spaces
import numpy as np

# KeysToDict from KeysToAdd


def keys_to_dict_calc(key_to_add, observation_space, player_to_skip="P2"):
    keys_to_dict = {}
    for key in key_to_add:
        elem_to_add = []
        # Loop among all spaces
        for k in observation_space.spaces:
            # Skip frame and consider only a single player
            if k == "frame" or k == player_to_skip:
                continue
            if isinstance(observation_space[k], gym.spaces.dict.Dict):
                for l in observation_space.spaces[k].spaces:
                    if isinstance(observation_space[k][l], gym.spaces.dict.Dict):
                        if key == l:
                            elem_to_add.append("Px")
                            elem_to_add.append(l)
                            keys_to_dict[key] = elem_to_add
                    else:
                        if key == l:
                            elem_to_add.append("Px")
                            elem_to_add.append(l)
                            keys_to_dict[key] = elem_to_add
            else:
                if key == k:
                    elem_to_add.append(k)
                    keys_to_dict[key] = elem_to_add

    return keys_to_dict

# Positioning element on last frame channel


def add_keys(counter, key_to_add, keys_to_dict, obs, new_data, player_id):

    data_pos = counter

    for key in key_to_add:
        tmp_list = keys_to_dict[key]
        if tmp_list[0] == "Px":
            val = obs["P{}".format(player_id+1)]

            for idx in range(len(tmp_list)-1):

                if tmp_list[idx+1] == "actions":
                    val = np.concatenate((val["actions"]["move"], val["actions"]["attack"]))
                else:
                    val = val[tmp_list[idx+1]]

                if isinstance(val, (float, int)) or val.size == 1:
                    val = [val]
        else:
            val = [obs[tmp_list[0]]]

        for elem in val:
            counter = counter + 1
            new_data[counter] = elem

    new_data[data_pos] = counter - data_pos

    return counter

# Observation modification (adding one channel to store additional info)


def process_obs(obs, dtype, box_high_bound, player_side, key_to_add,
                keys_to_dict, imitation_learning=False):

    # Adding a channel to the standard image, it will be in last position and
    # it will store additional obs
    shp = obs["frame"].shape
    obs_new = np.zeros((shp[0], shp[1], shp[2]+1), dtype=dtype)

    # Storing standard image in the first channel leaving the last one for
    # additional obs
    obs_new[:, :, 0:shp[2]] = obs["frame"]

    # Adding new info to the additional channel, on a very
    # long line and then reshaping into the obs dim
    new_data = np.zeros((shp[0] * shp[1]))

    # Adding new info for 1P
    counter = 0
    add_keys(counter, key_to_add, keys_to_dict, obs, new_data, player_id=0)

    # Adding new info for P2 in 2P games
    if player_side == "P1P2" and not imitation_learning:
        counter = int((shp[0] * shp[1]) / 2)
        add_keys(counter, key_to_add, keys_to_dict, obs, new_data, player_id=1)

    new_data = np.reshape(new_data, (shp[0], -1))

    new_data = new_data * box_high_bound

    obs_new[:, :, shp[2]] = new_data

    return obs_new

# Convert additional obs to fifth observation channel for stable baselines


class AdditionalObsToChannel(gym.ObservationWrapper):
    def __init__(self, env, key_to_add, imitation_learning=False):
        """
        Add to observations additional info
        :param env: (Gym Environment) the environment to wrap
        :param key_to_add: (list) ordered parameters for additional Obs
        """
        gym.ObservationWrapper.__init__(self, env)
        shp = self.env.observation_space["frame"].shape
        self.key_to_add = key_to_add
        self.imitation_learning = imitation_learning

        self.box_high_bound = self.env.observation_space["frame"].high.max()
        self.box_low_bound = self.env.observation_space["frame"].low.min()
        assert (self.box_high_bound == 1.0 or self.box_high_bound == 255),\
               "Observation space max bound must be either 1.0 or 255 to use Additional Obs"
        assert (self.box_low_bound == 0.0 or self.box_low_bound == -1.0),\
               "Observation space min bound must be either 0.0 or -1.0 to use Additional Obs"

        # Build key_to_add - Observation Space dict connectivity
        self.keys_to_dict = keys_to_dict_calc(self.key_to_add, self.env.observation_space)

        self.old_obs_space = self.observation_space
        self.observation_space = spaces.Box(low=self.box_low_bound, high=self.box_high_bound,
                                            shape=(shp[0], shp[1], shp[2] + 1),
                                            dtype=np.float32)
        self.shp = self.observation_space.shape

        # Return key_to_add count
        self.key_to_add_count = []
        for key in self.key_to_add:
            p1Val = add_keys(0, [key], self.keys_to_dict, self.old_obs_space.sample(),
                             np.zeros((shp[0] * shp[1])), 0)
            if self.env.player_side == "P1P2":
                p2Val = add_keys(0, [key], self.keys_to_dict, self.old_obs_space.sample(),
                                 np.zeros((shp[0] * shp[1])), 1)
                self.key_to_add_count.append([p1Val, p2Val])
            else:
                self.key_to_add_count.append([p1Val])

    # Process observation
    def observation(self, obs):

        return process_obs(obs, self.observation_space.dtype,
                           self.box_high_bound, self.env.player_side,
                           self.key_to_add, self.keys_to_dict,
                           self.imitation_learning)
