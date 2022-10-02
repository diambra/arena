from ..sb_utils import p2_to_p1_add_obs_move
import gym
import numpy as np

# Gym Env wrapper for two players mode to be used in integrated Self Play


class IntegratedSelfPlay(gym.Wrapper):
    def __init__(self, env):

        gym.Wrapper.__init__(self, env)

        # Modify action space
        assert self.action_space["P1"] == self.action_space["P2"],\
               "P1 and P2 action spaces are supposed to be identical: {} {}"\
                   .format(self.action_space["P1"], self.action_space["P2"])
        self.action_space = self.action_space["P1"]

# Gym Env wrapper for two players mode with RL algo on P2


class SelfPlayVsRL(gym.Wrapper):
    def __init__(self, env, p2_policy):

        gym.Wrapper.__init__(self, env)

        # Modify action space
        self.action_space = self.action_space["P1"]

        # P2 action logic
        self.p2_policy = p2_policy

    # Save last Observation
    def update_last_obs(self, obs):
        self.lastObs = obs

    # Update p2_policy RL policy weights
    def update_p2_policy_weights(self, weights_path):
        self.p2_policy.update_weights(weights_path)

    # Step the environment
    def step(self, action):

        # Observation modification and P2 actions selected by the model
        self.lastObs[:, :, -1] = p2_to_p1_add_obs_move(self.lastObs[:, :, -1])
        p2_policy_actions, _ = self.p2_policy.act(self.lastObs)

        obs, reward, done, info = self.env.step(np.hstack((action, p2_policy_actions)))
        self.update_last_obs(obs)

        return obs, reward, done, info

    # Reset the environment
    def reset(self):

        obs = self.env.reset()
        self.update_last_obs(obs)

        return obs

# Gym Env wrapper for two players mode with HUM+Gamepad on P2


class VsHum(gym.Wrapper):
    def __init__(self, env, p2_policy):

        gym.Wrapper.__init__(self, env)

        # Modify action space
        self.action_space = self.action_space["P1"]

        # P2 action logic
        self.p2_policy = p2_policy

        # If p2 action logic is gamepad, add it to self.gamepads (for char selection)
        # Check action space is prescribed as "multi_discrete"
        self.p2_policy.initialize(self.env.actionList())
        if self.actionsSpace[1] != "multi_discrete":
            raise Exception("Action Space for P2 must be \"multi_discrete\" when using gamePad")
        if not self.attackButCombination[1]:
            raise Exception("Use attack buttons combinations for P2 must be \"True\" when using gamePad")

    # Step the environment
    def step(self, action):

        # P2 actions selected by the Gamepad
        p2_policy_actions, _ = self.p2_policy.act()

        return self.env.step(np.hstack((action, p2_policy_actions)))
