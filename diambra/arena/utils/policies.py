# Collection of policies to be applied on the environment
import numpy as np
import random
import logging

# No action policy


class NoActionPolicy(object):

    def __init__(self, name="No Action", action_space="multiDiscrete"):
        self.id = "noAction"
        self.name = name
        self.action_space = action_space

    def initialize(self):
        pass

    def reset(self, observation):
        pass

    def act(self, observation, info=None):

        if self.action_space == "multiDiscrete":
            prob = [1.0, 1.0]
            action = [0, 0]
        else:
            prob = [1.0, 1.0]
            action = 0

        return action, prob

# Random policy, sampling from the action space


class RandomPolicy(object):

    def __init__(self, n_actions, name="Random", action_space="multiDiscrete"):
        self.n_actions = np.array(n_actions)
        self.id = "random"
        self.name = name
        self.action_space = action_space

    def initialize(self):
        pass

    def reset(self, observation):
        pass

    def act(self, observation, info=None):

        prob = 1.0/self.n_actions

        if self.action_space == "discrete":
            action = random.randrange(self.n_actions[0]+self.n_actions[1]-1)
        else:
            action = []
            for idx in range(self.n_actions.shape[0]):
                action.append(random.randrange(self.n_actions[idx]))

        return action, prob

# RL Policy, which uses a model to select the action


class RLPolicy(object):

    def __init__(self, model, deterministic_flag,
                 n_actions, name="Generic RL", action_space="multiDiscrete"):

        self.n_actions = n_actions
        self.deterministic_flag = deterministic_flag
        self.model = model
        self.id = "rl"
        self.name = name
        self.action_space = action_space
        self.logger = logging.getLogger(__name__)

    def initialize(self):
        pass

    def reset(self, observation):
        pass

    def update_weights(self, weights_path):
        self.logger.debug("Loading new weights: {}".format(weights_path))
        self.model.load_parameters(weights_path)

    def act(self, observation, info=None):
        action_prob = self.model.action_probability(observation)

        # if self.deterministic_flag:
        #   action = np.argmax(action_prob)
        # else:
        #   if self.action_space == "discrete":
        #       action = np.random.choice([x for x in range(len(action_prob))],
        #                                 p=action_prob)
        #   else:
        #       action = self.model.predict(observation,
        #                                   deterministic=self.deterministic_flag)
        action, _ = self.model.predict(
            observation, deterministic=self.deterministic_flag)
        action = action.tolist()

        prob = action_prob
        if self.action_space == "discrete":

            if action >= self.n_actions[0]:
                prob = [0.0, action_prob[action]]
            else:
                prob = [action_prob[action], 0.0]
        else:

            prob = action_prob
            # self.logger.error("Warning!! Probabilities for
            #        MultiDiscrete are not correct!")
            # Can be ok doing nothing, but better to check
            # raise Exception("To be checked")

        return action, prob

# Human policy, retrieved via GamePad


class GamepadPolicy(object):

    def __init__(self, gamepad_class, name="Human"):
        self.gamepad_class = gamepad_class
        self.id = "gamepad"
        self.initialized = False
        self.name = name

    def initialize(self, action_list, gamepad_num=0):
        if not self.initialized:
            self.gamepad = self.gamepad_class(action_list=action_list,
                                              gamepad_num=gamepad_num)
            self.gamepad.start()
            self.initialized = True

    def reset(self, observation):
        pass

    def get_actions(self):
        return self.gamepad.get_actions()

    def act(self, observation, info=None):

        prob = [1.0, 1.0]
        action = self.gamepad.get_actions()

        return action, prob
