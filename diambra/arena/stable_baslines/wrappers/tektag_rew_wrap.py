import gym

# Gym Env wrapper to penalize for char 2 health at round end


class TektagRoundEndChar2Penalty(gym.Wrapper):
    def __init__(self, env):

        gym.Wrapper.__init__(self, env)

        # Check ownHealth2 is available
        assert (("Health1P1" in self.add_obs.keys()) and
                ("Health1P2" in self.add_obs.keys()) and
                ("Health2P1" in self.add_obs.keys()) and
                ("Health2P2" in self.add_obs.keys())),\
               "Both first and second char healths, for both P1 and P2, must be present in add_obs" +\
               " to use tektagRoundEndChar2Penalty wrapper {}".format(self.add_obs.keys())

        # Check single player mode is on
        assert (isinstance(self.action_space, gym.spaces.MultiDiscrete) or
                isinstance(self.action_space, gym.spaces.Discrete)),\
               "Only single player environment are supported by" +\
               " tektagRoundEndChar2Penalty wrapper, {}".format(type(self.action_space))

        print("Applying Background Char Health Penalty at Round End Wrapper")

    # Step the environment
    def step(self, action):

        obs, reward, done, info = self.env.step(action)

        # When round ends
        if info["round_done"] is True:
            # If round lost
            if reward < 0.0:
                # Add penalty for background character health bar
                # print("Applying end round penalty: original reward = {},"\
                #      " reward with penalty = {}".format(round(reward, 2), round(- 2.0*self.oldHealths, 2)))
                reward = - 2.0*self.oldHealths

        self.oldHealths = obs["P1"]["ownHealth1"] + obs["P1"]["ownHealth2"]

        return obs, reward, done, info

    # Reset the environment
    def reset(self):

        obs = self.env.reset()

        # Variable to store previous step healths
        self.oldHealths = obs["P1"]["ownHealth1"] + obs["P1"]["ownHealth2"]

        return obs

# Gym Env wrapper to penalize when background char has health bar a lot higher
# than foreground char


class TektagHealthBarUnbalancePenalty(gym.Wrapper):
    def __init__(self, env, unbalance_thresh=0.75):

        gym.Wrapper.__init__(self, env)

        # Check ownHealth2 is available
        assert (("Health1P1" in self.add_obs.keys()) and
                ("Health1P2" in self.add_obs.keys()) and
                ("Health2P1" in self.add_obs.keys()) and
                ("Health2P2" in self.add_obs.keys())),\
               "Both first and second char healths, for both P1 and P2, must be present in add_obs" +\
               " to use tektagRoundEndChar2Penalty wrapper {}".format(self.add_obs.keys())

        # Check single player mode is on
        assert (isinstance(self.action_space, gym.spaces.MultiDiscrete) or
                isinstance(self.action_space, gym.spaces.Discrete)),\
               "Only single player environment are supported by" +\
               " tektagRoundEndChar2Penalty wrapper, {}".format(type(self.action_space))

        print("Applying Char Health Unbalance Penalty Wrapper")

        self.unbalance_thresh = unbalance_thresh
        self.penalty = 0.1*self.unbalance_thresh
        self.charManagement = [["ownHealth1", "ownHealth2"], ["ownHealth2", "ownHealth1"]]

    # Step the environment
    def step(self, action):

        obs, reward, done, info = self.env.step(action)

        # If background char health minus foreground one is
        # higher than threshold
        keys = self.charManagement[obs["P1"]["ownActiveChar"]]
        if ((obs["P1"][keys[1]] - obs["P1"][keys[0]]) > (self.unbalance_thresh / 2.0)):
            # Add penalty for background character health bar
            # print("Applying Health unbalance penalty: penalty = {}".format(-round(self.penalty, 2)))
            reward = -self.penalty

        return obs, reward, done, info
