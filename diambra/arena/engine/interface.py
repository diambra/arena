import numpy as np
import os
import logging

from diambra.engine import Client, model
import grpc

CONNECTION_FAILED_ERROR_TEXT = """DIAMBRA Arena failed to connect to the Engine Server.
 - If you are running a Python script, are you running with DIAMBRA CLI: `diambra run python script.py`?
 - If you are running a Python Notebook, have you started Jupyter Notebook with DIAMBRA CLI: `diambra run jupyter notebook`?

See the docs (https://docs.diambra.ai) for additional details, or join DIAMBRA Discord Server (https://diambra.ai/discord) for support."""

# DIAMBRA Env Gym
class DiambraEngine:
    """Diambra Environment gym interface"""

    def __init__(self, env_address, grpc_timeout=60):
        self.logger = logging.getLogger(__name__)

        try:
            # Opening gRPC channel
            self.logger.info("Trying to connect to DIAMBRA Engine server (timeout={}s)...".format(grpc_timeout))
            self.client = Client(env_address, grpc_timeout)
        except grpc.FutureTimeoutError as e:
            raise Exception(CONNECTION_FAILED_ERROR_TEXT) from e

        self.logger.info("... done.")

    # Send env settings, retrieve env info and int variables list [pb low level]
    def env_init(self, env_settings_pb):
        try:
            response = self.client.EnvInit(env_settings_pb)
        except:
            try:
                response = self.client.GetError(model.Empty())
                exceptionMessage = "Received error message from engine: " + response.errorMessage
                self.logger.error(exceptionMessage)
            except:
                raise Exception(CONNECTION_FAILED_ERROR_TEXT)

        return response

    # Reset the environment [pb low level]
    def reset(self, episode_settings):
        return self.client.Reset(episode_settings)

    # Step the environment [pb low level]
    def step(self, action_list):
        actions = model.Actions()
        for action in action_list:
            action = model.Actions.Action(move=action[0], attack=action[1])
            actions.actions.append(action)
        return self.client.Step(actions)

    # Closing DIAMBRA Arena
    def close(self):
        response = self.client.Close(model.Empty())
        self.client.channel.close()
        return response
